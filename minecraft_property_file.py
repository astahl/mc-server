from datetime import datetime, timezone

def parse_property_line(line):
    commentStart = line.find("#")
    kvp = line[:commentStart]
    comment = line[commentStart + 1:-1].strip()
    key = value = None
    if kvp.count("=") > 0:    
        [key, value] = kvp.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value == '':
            value = None
        elif value.lower() == "true":
            value = True
        elif value.lower() == "false":
            value = False
        elif value.isnumeric():
            value = int(value)
        else:
            try:
                floatVal = float(value)
                value = floatVal
            except:
                value = value
    return [key, value, comment]

def make_property_line(key: str, value):
    valString = str(value)
    if type(value) is bool:
        valString = valString.lower()

    return key + "=" + valString + "\n"

def read_to_dict(file):
    properties = dict()
    with open(file, 'r') as f:
        for line in f.readlines():
            [key, value, comment] = parse_property_line(line)
            if key is not None:
                properties[key] = value
    return properties

def write(file, properties: dict, header_comment):
    with open(file, "w") as f:
        f.write("#" + header_comment + "\n")
        f.write("#" + datetime.now(timezone.utc).strftime("%a %b %d %H:%M:%S %Z %Y") + "\n")
        f.writelines([make_property_line(key, value) for key, value in properties.items()])

