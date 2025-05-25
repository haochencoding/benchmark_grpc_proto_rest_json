# Model summary

| Statistic             | Value                       |
| --------------------- | --------------------------- |
| Model                 | Mixed‐Effects Linear (REML) |
| Dependent variable    | `log_throughput`            |
| No. observations      | 2100                        |
| No. groups            | 21                          |
| Min. group size       | 100                         |
| Max. group size       | 100                         |
| Mean group size       | 100.0                       |
| Scale (residual var.) | 0.0001                      |
| Log-likelihood        | 6559.4547                   |
| Converged             | Yes                         |

# Fixed- and random-effect estimates
| Effect                                      | Estimate | Std. Error |    *z* | *p*-value | 95 % CI lower | 95 % CI upper | Signif |  Type  |
| ------------------------------------------- | -------: | ---------: | -----: | --------: | ------------: | ------------: | :----: | :----: |
| Intercept                                   |    2.359 |      0.010 | 232.89 |    <0.001 |         2.339 |         2.379 | \*\*\* |  Fixed |
| Protocol = *rest\_json*                     |   –0.148 |      0.014 | –10.37 |    <0.001 |        –0.177 |        –0.120 | \*\*\* |  Fixed |
| Protocol = *rest\_proto*                    |   –0.176 |      0.014 | –12.29 |    <0.001 |        –0.204 |        –0.148 | \*\*\* |  Fixed |
| Size = 10                                   |    1.003 |      0.014 |  70.00 |    <0.001 |         0.975 |         1.031 | \*\*\* |  Fixed |
| Size = 100                                  |    1.989 |      0.014 | 138.81 |    <0.001 |         1.960 |         2.017 | \*\*\* |  Fixed |
| Size = 1 000                                |    2.887 |      0.014 | 201.55 |    <0.001 |         2.859 |         2.915 | \*\*\* |  Fixed |
| Size = 10 000                               |    3.394 |      0.014 | 236.94 |    <0.001 |         3.366 |         3.422 | \*\*\* |  Fixed |
| Size = 100 000                              |    3.504 |      0.014 | 244.64 |    <0.001 |         3.476 |         3.532 | \*\*\* |  Fixed |
| Size = 1 000 000                            |    3.507 |      0.014 | 244.80 |    <0.001 |         3.479 |         3.535 | \*\*\* |  Fixed |
| Protocol × Size (*rest\_json* × 10)         |   –0.004 |      0.020 |  –0.19 |     0.846 |        –0.044 |         0.036 |        |  Fixed |
| Protocol × Size (*rest\_proto* × 10)        |   –0.003 |      0.020 |  –0.16 |     0.871 |        –0.043 |         0.036 |        |  Fixed |
| Protocol × Size (*rest\_json* × 100)        |   –0.018 |      0.020 |  –0.87 |     0.387 |        –0.057 |         0.022 |        |  Fixed |
| Protocol × Size (*rest\_proto* × 100)       |    0.003 |      0.020 |   0.15 |     0.879 |        –0.037 |         0.043 |        |  Fixed |
| Protocol × Size (*rest\_json* × 1 000)      |   –0.123 |      0.020 |  –6.08 |    <0.001 |        –0.163 |        –0.084 | \*\*\* |  Fixed |
| Protocol × Size (*rest\_proto* × 1 000)     |    0.032 |      0.020 |   1.59 |     0.112 |        –0.007 |         0.072 |        |  Fixed |
| Protocol × Size (*rest\_json* × 10 000)     |   –0.313 |      0.020 | –15.43 |    <0.001 |        –0.352 |        –0.273 | \*\*\* |  Fixed |
| Protocol × Size (*rest\_proto* × 10 000)    |    0.121 |      0.020 |   5.99 |    <0.001 |         0.082 |         0.161 | \*\*\* |  Fixed |
| Protocol × Size (*rest\_json* × 100 000)    |   –0.385 |      0.020 | –19.03 |    <0.001 |        –0.425 |        –0.346 | \*\*\* |  Fixed |
| Protocol × Size (*rest\_proto* × 100 000)   |    0.166 |      0.020 |   8.19 |    <0.001 |         0.126 |         0.206 | \*\*\* |  Fixed |
| Protocol × Size (*rest\_json* × 1 000 000)  |   –0.397 |      0.020 | –19.61 |    <0.001 |        –0.437 |        –0.357 | \*\*\* |  Fixed |
| Protocol × Size (*rest\_proto* × 1 000 000) |    0.160 |      0.020 |   7.91 |    <0.001 |         0.121 |         0.200 | \*\*\* |  Fixed |
| **Batch variance**                          |    0.000 | 58 000.193 |      — |         — |             — |             — |        | Random |

Significance key: *** p < 0.001, ** p < 0.01, * p < 0.05
