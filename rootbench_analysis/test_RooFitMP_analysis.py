import RooFitMP_analysis
import pandas as pd
import numpy as np

df_fake = pd.DataFrame({'worker_id': [0, 0, 0, 1, 1, 1, 2, 2, 2],
                        'task': range(9),
                        'NumCPU': np.ones(9) * 3,
                        'benchmark_number': np.ones(9),
                        'gradient number': np.ones(9),
                        'time [s]': np.ones(9)})

RooFitMP_analysis.plot_partial_derivative_per_gradient(df_fake, figsize=(7, 7))
