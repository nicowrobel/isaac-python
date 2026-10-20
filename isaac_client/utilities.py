import numpy as np
import matplotlib.pyplot as plt


def alpha_fct_default(value):
    """
    default alpha function that converts a x in [0, 1] to an alpha valaue [0,1]
    this is a default and example implementation
    """
    if value < 0.05:
        return 0.0
    else:
        return 0.8 * value**0.5

def createTransferFunction(colorMap,
                           alpha_fct = alpha_fct_default,
                           N_samples = 10):
    """
    convert a matplotlib cmap to a ISAAC rgba dict for use in the transfer function

    colorMap ... matplotlib cmap
    alpha ... a function of f(x)->[0,1] for x in [0,1] for alpha values
    N_samples ... number of equidistant sample points for the ISAAC rgba dict [default: 10]
    """
    rgba = []
    isaac_scaling = 1024
    
    for value in np.linspace(0,1,N_samples):
        r,g,b = colorMap(value)[:3]
        new_dict = {'value': value * isaac_scaling,
                    'r': r, 'g': g, 'b': b, 'a': alpha_fct(value) }
        rgba.append(new_dict)

    return rgba


if __name__ == "__main__":
    print("Example ISAAC tranfer function using a the inferno cmap:")
    rgba_example = createTransferFunction(plt.cm.inferno, lambda x: 0.1 + x * 0.9, 12)
    print(rgba_example)
    
