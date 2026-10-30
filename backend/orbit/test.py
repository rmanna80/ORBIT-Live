field = "-11606-4"
sign = -1 if field[0] == "-" else 1 
field = field.lstrip("+-")
mantissa = field[:-2]
exponent = field[-2:]
number = float("0." + mantissa)

print(number)



def parse_tle(name, line1, line2):
    line1 = line1.strip()
    line2 = line2.strip()
    if len(line1) != 69 or len(line2) != 69:
        return "Invalid TLE length"

    norad_id = int(line1[2:7])
    inclination = float(line2[8:16])
    mean_motion = float(line2[52:63])
    
    print(name)
    print(norad_id)
    print(inclination)
    print(mean_motion)
    
name = "ISS (ZARYA)"
line1 = "1 25544U 98067A   26303.81643194  .00016717  00000-0  31497-3 0  9997"
line2 = "2 25544  51.6421  21.2844 0001124  42.5631  57.4369 15.49428513565017"

parse_tle(name, line1, line2)
        
