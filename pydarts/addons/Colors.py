
import random
# Code complet sans les nuances ,


Colors={
'red' : (255, 0, 0),
'green' : (0, 255, 0),
'blue' : (0, 0, 255),
'white' : (255, 255, 255),
'gold' : (255, 215, 0),
'cyan' : (0, 255, 255),
'magenta' : (255, 0, 255),
'yellow' : (255, 255, 0),
'orange' : (255, 165, 0),

'darkred' : (139, 0, 0),
'darkgreen' : (0, 100, 0),
'darkblue' : (0, 0, 139),
'darkgoldenrod' : (184, 134, 11),
'darkcyan' : (0, 139, 139),
'darkmagenta' : (139, 0, 139),
'darkorange' : (255, 140, 0),

'aquamarine' : (127, 255, 212),
'black' : (0, 0, 0),
'blueviolet' : (138, 43, 226),
'brown' : (165, 42, 42),
'burlywood' : (222, 184, 135),
'cadetblue' : (95, 158, 160),
'chartreuse' : (127, 255, 0),
'chocolate' : (210, 105, 30),
'coral' : (255, 127, 80),
'cornflowerblue' : (100, 149, 237),
'darkkhaki' : (189, 183, 107),
'darkorchid' : (153, 50, 204),
'darksalmon' : (233, 150, 122),
'darkslateblue' : (72, 61, 139),
'darkturquoise' : (0, 206, 209),
'darkviolet' : (148, 0, 211),
'deeppink' : (255, 20, 147),
'deepskyblue' : (0, 191, 255),
'dodgerblue' : (30, 144, 255),
'firebrick' : (178, 34, 34),
'forestgreen' : (34, 139, 34),
'goldenrod' : (218, 165, 32),
'greenyellow' : (173, 255, 47),
'hotpink' : (255, 105, 180),
'indianred' : (205, 92, 92),
'khaki' : (240, 230, 140),
'lawngreen' : (124, 252, 0),
'lightcoral' : (240, 128, 128),
'lightgoldenrod' : (238, 221, 130),
'lightgreen' : (144, 238, 144),
'lightpink' : (255, 182, 193),
'lightsalmon' : (255, 160, 122),
'lightseagreen' : (32, 178, 170),
'lightskyblue' : (135, 206, 250),
'lightslateblue' : (132, 112, 255),
'limegreen' : (50, 205, 50),
'maroon' : (176, 48, 96),
'mediumaquamarine' : (102, 205, 170),
'mediumblue' : (0, 0, 205),
'mediumorchid' : (186, 85, 211),
'mediumpurple' : (147, 112, 219),
'mediumseagreen' : (60, 179, 113),
'mediumslateblue' : (123, 104, 238),
'mediumspringreen' : (0, 250, 154),
'mediumturquoise' : (72, 209, 204),
'mediumvioletred' : (199, 21, 133),
'midnightblue' : (25, 25, 112),
'moccasin' : (255, 228, 181),
'navajowhite' : (255, 222, 173),
'navy' : (0, 0, 128),
'navyblue' : (0, 0, 128),
'olivedrab' : (107, 142, 35),
'orangered' : (255, 69, 0),
'orchid' : (218, 112, 214),
'palegoldenrod' : (238, 232, 170),
'palegreen' : (152, 251, 152),
'palevioletred' : (219, 112, 147),
'peachpuff' : (255, 218, 185),
'peru' : (205, 133, 63),
'purple' : (160, 32, 240),
'royalblue' : (65, 105, 225),
'saddlebrown' : (139, 69, 19),
'salmon' : (250, 128, 114),
'sandybrown' : (244, 164, 96),
'seagreen' : (46, 139, 87),
'sienna' : (160, 82, 45),
'silver' : (192,192,192),
'skyblue' : (135, 206, 235),
'slateblue' : (106, 90, 205),
'springreen' : (0, 255, 127),
'steelblue' : (70, 130, 180),
'tan' : (210, 180, 140),
'tomato' : (255, 99, 71),
'turquoise' : (64, 224, 208),
'verydarkgreen' : (0, 32, 0),
'verydarkred' : (32, 0, 0),
'violet' : (238, 130, 238),
'violetred' : (208, 32, 144),
'wheat' : (245, 222, 179),
'yellowgreen' : (154, 205, 50),
}

class CColors(object):
    def __init__(self):
        C={}
        self.Colors={}
        for c in Colors:
            self.Colors[c] = (int(Colors[c][0]), int(Colors[c][1]), int(Colors[c][2]))

    def GetColor(self, c=None):
        if c == None or c == 'random' :
            Clist = list(self.Colors.items())
            c = random.choice(Clist)[0]
        elif ',' in c:
            # Alreadu in good format
            return (int(c.replace('(', '').split(',')[0]), int(c.split(',')[1]), int(c.replace(')', '').split(',')[2]))
        return self.Colors[c]

    def MultColor(self, Color, Mult):
        return (int(abs(float(Color[0])) * Mult), int(abs(float(Color[1])) * Mult), int(abs(float(Color[2])) * Mult))

    def ShakeColor(self, Color, Shack):
        if Shack % 3 == 0:
            return Color
        elif Shack % 3 == 1:
            return (Color[1] , Color[2] , Color[0])
        else :
            return (Color[2] , Color[0] , Color[1])

