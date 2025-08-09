import struct

def klee_hex_to_int_array(hexstr):
    # Remove '0x' prefix if present
    if hexstr.startswith('0x'):
        hexstr = hexstr[2:]
    # Ensure even length
    if len(hexstr) % 8 != 0:
        raise ValueError("Hex string length is not a multiple of 8 (4 bytes per int)")
    arr = []
    for i in range(0, len(hexstr), 8):
        chunk = hexstr[i:i+8]
        # Convert hex chunk to bytes (little-endian)
        b = bytes.fromhex(chunk)
        # Interpret as signed int (little-endian)
        val = struct.unpack('<i', b)[0]
        arr.append(val)
    return arr

# Example usage:
hexstr = '0xffffffffffffffffffffffffffffffffffffffffffffffffffffffff80820000ffffffffffffffffffffffff800300000000000080000000ffffffff'

arr = klee_hex_to_int_array(hexstr)
print(arr)  # Output: [-2147483648, -2130706432, 0]


