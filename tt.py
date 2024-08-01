
sz_of_sz = 3
size = 1807

neck = size.to_bytes(sz_of_sz, 'big', signed=False)

reverted = int.from_bytes(neck, 'big', signed=False)

print(neck, size, reverted)
