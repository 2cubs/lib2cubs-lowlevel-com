# lib2cubs-lowlevel-com
Multipurpose Communication Library


## Low-Level part
### General description
The App-Frame/Message/Package is the sequence of bytes that represents the content
that one side is transferring to another and vice-versa. 

It's a low-level exchange mechanism, that adds minimum of additional payload
to the content, convert everything to the sequence of bytes due sending and
due receiving getting the sequence, reading it and processing to get the original
content.

This mechanism does not define the particular High-Level interpretation or meaning,
So anybody who want's to implement their own High-Level protocol are fully welcome.
Such separation of the levels allow to do not limit others to our way of thinking 
(by using only json for messages/RPCs exchange) and to do not limit ourselves to use XML or YAML
in case of our need.

**Important**: Keep in mind, that different App-Frame Types have different decoding/encoding procedure.
For example Stream of bytes can't be expected to work the same way as Simple Message.

### Choices and considerations
 * **Why using "json" instead of native python pickle format?**
    1. Because the protocol suppose to be lightweight, but easily adaptable across different
       languages and technologies. So if the Server or Client implementation will go with "C/C++"
       They should not implement "pickle" parser or use additional libraries just for that purpose.
       Json - is simple and pretty much native across all the languages and technologies.
    2. Flexibility of this approach allows to use pickle format as an underlying format encapsulated string.
       Or to use pickle format through extending the protocol and providing mime type metadata flag, specifying
       what is the content of the payload. 
 * **Why exactly this format of the App-Frame?**
    * It's simple and flexible. It might be less efficient than other formats, but I wanted to implement
      it exactly this way, because I consider it as a combination of flexibility, modularity and 
      extensibility. So it's well thought through but personal choice. 
      Any improvements are welcome!
 * **Why splitting the first byte of a frame by 4 bit's value each?**
    * To reduce redundant bytes being sent. Value of 4 bits for af-type is more than enough,
      and 4 bits for size-of-size is more than enough as well. So benefit 
      of sparing 1 additional byte per frame is obvious! :D
 * **Why using base64 encoding for metadata and why json inside?**
    * About json - is exactly the same answer as above in the very first bullet point
    * About base64 - It's not the most efficient format for the exchange, but it allows to simplify
      parsing and separating the payload and the metadata simply by "\n" symbol. With all
      mentioned above with a careful usage of metadata field - it might be a comfortable way
      to work with. And Base64 format protects from having "\n" symbol breaking the format 
      (due to alphabet of the Base64 encoding)

### App-Frame types (af-type)
App-Frame type is represented by first 4 bits of 
the first byte (byteorder=big) of the transmitting sequence of bytes.

Depending on the af-type the processing procedure can vary

1.  **0x0** - Ping/Pong frame
2.  **0x1** - Simple frame
3.  **0x2** - [_Reserved_]
4.  **0x3** - [_Reserved_]
5.  **0x4** - [_Reserved_]
6.  **0x5** - [_Reserved_]
7.  **0x6** - [_Reserved_]
8.  **0x7** - [_Reserved_]
9.  **0x8** - [_Reserved_]
10. **0x9** - Stream
11. **0xA** - (_Free to use_)
12. **0xB** - (_Free to use_)
13. **0xC** - (_Free to use_)
14. **0xD** - (_Free to use_)
15. **0xE** - (_Free to use_)
16. **0xF** - (_Free to use_)

the last 4 bits of the first byte (byteorder=big) are being "Size-Of-Size". It means that it stores
The value from 0 to 15 specifying amount of bytes defined for Size of the content. 
So basically it stores size of the size of the content (Don't ask why I did it this way, let's just assume 
that I'm a crazy person).

The first 10 types (0x0 - 0x9) are reserved for the needs of the library developers,
we kindly ask you to do not use them.

If you really sure that you want to create your own types (and processors for them)
You can use one or few from the last part of the range, values 0xA - 0xF are free to use
for you. In case you would need more than 6 types, you could simply use just 1 of those and 
specify your own custom "types"/"sub-types" under it's format.

### Each type format description

#### For all af-types
 1.  First 4 bits of the first byte (byteorder=big) is af-type
 2.  Last 4 bits of the first byte (byteorder=big) is "Size-Of-Size"
 3.  Following amount of bytes (amount specified in the "Size-Of-Size" 4 bits earlier)
     defining the size of the payload/content (The size must specify the length of the known 
     size of the payload after "\n" symbol)
 4.  Then suppose to go or skipped base64 data representing metadata key=value pairs, 
     and then "\n" symbol ("\n" symbol must be presented even if there is no metadata,
     this symbol means end of "head" part of the frame, and starting the payload)
 5.  From here goes content/payload/stream

**Important 1**: Described above is standard for all the frames, so you have to follow the same
logic if you plan to implement your own custom af-types

**Important 2**: Despite the fact that all the af-types follow described above rules,
Stream af-type might have 0-size field, which will not affect the stream delivery, 
because Stream is being constantly sending (This is why it must be done in a separate 
(control) channel, because it's not possible to break it from within the channel). 
The same time.

**Important 3**: Strongly recommended to avoid using too much of metadata field when possible. Base64 encoding
has impact on the performance and size. Basically it is needed only for the general cases like holding 
frame's key information or the alias of the frame. In some cases of the file transferring or 
the basic stream description.

Reg-ex "text-o-gram" of the format would be:

`(HEAD)\n(BODY)` / `(0x?0x?)[0-9]*[A-Za-z0-9]*\n(.*)`

HEAD part: 
 * `(0x?0x?)` - one byte (contains af-type and size-of-size field)  
 * `[0-9]*` - zero to 15 bytes of unsigned integer depending on the size-of-size field (contains size of payload field)
 * `[A-Za-z0-9]*` - Base64 text-data, or absent (contains metadata field)
 * `\n` - Defining end of the HEAD part

BODY part: 
 * `(.*)` - Payload/Content  


#### **0x0** - Ping/Pong frame
This is a super simple frame containing only one metadata key/value pair with key name **PING=** or **PONG=**
and the value of md5 of the payload (which could be empty, then the md5 hash must be of the empty string, 
and size field must be 0). The payload will be used only for comparing hashes, and basically ignored completely.


#### **0x1** - Simple frame
Simple frames are used for control channel and for other channels as well to exchange messages
and data in different formats (including binary), the mostly textual like: JSON, XML, etc.
or any binary. The mime type and/or other additional data is defined through metadata field.

The empty metadata frame would be considered as one-way (expecting no response) message in JSON
format (Notification-like). That is not preferred way of sending frames, but it is allowed as
an option. Because there is no metadata with frame's key and additional information about
the message - it's not possible to refer to this message on the other side, this is why it's
just a one-way message.

This af-type is the major of all, it is used to implement RPC, etc.


#### **0x9** - Stream
This is a really special af-type. After the head-part ending by "\n" symbol, there goes infinite stream of data.
This af-type allows to implement Audio/Video, Screencasting, Streamed data delivery. It can't be used without having
the control channel opened. Because the end of the streaming can be triggered only by 
the signaling frames (Simple frames in the control channel). So Stream shouldn't be used standalone.