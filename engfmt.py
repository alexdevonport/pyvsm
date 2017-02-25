import math



def splitExpMantissa(x):
    exp = round(math.log10(x))
    mantissa = x / math.pow(10, exp)
    return exp, mantissa


print(splitExpMantissa(1234.5))
print(splitExpMantissa(0.000314))
