import numpy as np
import matplotlib.pyplot as plt


def createTransferFunction(colorMap,
                           N_samples = 10):
                           alpha_fct = lambda x: x,
    """
    convert a matplotlib cmap to a ISAAC rgba dict for use in the transfer function

    colorMap ... matplotlib cmap
    alpha_fct ... a function of f(x)->[0,1] for x in [0,1] for alpha values [default: f(x)=x]
    N_samples ... number of equidistant sample points for the ISAAC rgba dict [default: 10]
    isaac_scaling ... scaling factor used by ISAAC [default: 1024]
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
    
