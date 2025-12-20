import struct

def is_fast_start(file_path):
    """Checks if 'moov' atom is before 'mdat' atom."""
    with open(file_path, "rb") as f:
        while True:
            # Read atom size (4 bytes) and type (4 bytes)
            header = f.read(8)
            if len(header) < 8:
                break
            
            atom_size = struct.unpack(">I", header[:4])[0]
            atom_type = header[4:].decode("utf-8")

            if atom_type == "moov":
                return True  # Fast Start!
            if atom_type == "mdat":
                return False # Slow Start (mdat came before moov)
            
            # Skip to next atom (size includes the 8 header bytes)
            # 0 size means 'until end of file', 1 means extended size (64-bit)
            if atom_size == 1:
                # Read extended size (8 bytes)
                atom_size = struct.unpack(">Q", f.read(8))[0]
                f.seek(atom_size - 16, 1) # Seek forward, skipping header
            elif atom_size == 0:
                break # Last atom
            else:
                f.seek(atom_size - 8, 1) # Seek forward

    return False # Default fallback


print(is_fast_start("/Users/nirmal/Downloads/samplvid.mp4"))