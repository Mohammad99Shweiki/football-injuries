# Phase 6: Injury profiles per style

Generated 2026-10-25 by `notebooks/06_injury_profiles.ipynb`, where each step is shown with its checks.

## Key numbers

- 24,581 injuries > 7 days in 1,170 team-seasons; 17,283 with a known type, 17,056 with a known location.
- **RQ-P1 (does the mix differ by style?):** attack × type: p = 0.0923, V = 0.022; attack × location: p = 0.0129, V = 0.031; attack × pattern: p = 0.0001, V = 0.036; attack × severity: p = 0.0001, V = 0.063; defence × type: p = 0.0195, V = 0.024; defence × location: p = 0.0001, V = 0.036; defence × pattern: p = 0.0001, V = 0.037; defence × severity: p = 0.0001, V = 0.061.
- **RQ-P2 (which patterns?):** 184 style × category tests; 18 findings at q < 0.05, 1 of them robust to position and team strength.
- **RQ-P3 (injury-profile groups):** usable k: 2, 3, 4; chosen k = 2; silhouette 0.117 vs null 95th percentile 0.077; agreement with attacking style V = 0.074 (p = 0.114; within strength 0.437), defensive style V = 0.106 (p = 0.0049; within strength 0.0699), strength V = 0.099, league V = 0.042.

## 1. Categories

| family | category | injuries | share of its denominator |
|---|---|---|---|
| type | muscle | 11416 | 0.661 |
| type | ligament/joint | 2134 | 0.123 |
| type | impact | 1802 | 0.104 |
| type | fracture/bone | 843 | 0.049 |
| type | tendon | 560 | 0.032 |
| type | other | 528 | 0.031 |
| location | knee | 3624 | 0.212 |
| location | hamstring | 3249 | 0.19 |
| location | groin/adductor/hip | 2305 | 0.135 |
| location | ankle | 2155 | 0.126 |
| location | calf/achilles/lower leg | 1882 | 0.11 |
| location | thigh | 1069 | 0.063 |
| location | upper body | 1023 | 0.06 |
| location | foot/toe | 837 | 0.049 |
| pattern | muscle · hamstring | 3244 | 0.132 |
| pattern | muscle · groin/adductor/hip | 1676 | 0.068 |
| pattern | muscle · calf/achilles/lower leg | 1350 | 0.055 |
| pattern | ligament/joint · knee | 1242 | 0.051 |
| pattern | muscle · thigh | 723 | 0.029 |
| pattern | ligament/joint · ankle | 566 | 0.023 |
| pattern | impact · thigh | 342 | 0.014 |
| pattern | tendon · calf/achilles/lower leg | 326 | 0.013 |
| severity | severe | 10993 | 0.447 |

## 2. Does the mix differ by style? (omnibus permutation tests)

| phase | family | categories | injuries | T | shuffled T (median) | p | V |
|---|---|---|---|---|---|---|---|
| attack | type | 6 | 17283 | 26.17 | 16.4194 | 0.0923 | 0.0225 |
| attack | location | 9 | 17056 | 47.9446 | 26.4394 | 0.0129 | 0.0306 |
| attack | pattern | 9 | 24581 | 93.8129 | 29.7014 | 0.0001 | 0.0357 |
| attack | severity | 2 | 24581 | 97.7071 | 3.3727 | 0.0001 | 0.063 |
| defence | type | 6 | 17283 | 30.363 | 14.9713 | 0.0195 | 0.0242 |
| defence | location | 9 | 17056 | 65.7283 | 24.0408 | 0.0001 | 0.0358 |
| defence | pattern | 9 | 24581 | 103.1655 | 27.6834 | 0.0001 | 0.0374 |
| defence | severity | 2 | 24581 | 91.7238 | 3.0578 | 0.0001 | 0.0611 |

## 3. Profile ratios (observed ÷ expected from league × season; 95% CI over clubs)

![Profile ratios](figures/06_profile_ratios.png)

### Findings (Benjamini–Hochberg q < 0.05)

| phase | style | family | category | observed | expected | ratio | low | high | q (BH) | ratio + position | ratio + position + strength | adjusted low | adjusted high | robust |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| attack | Build-up into the box | pattern | impact · thigh | 77 | 123.558 | 0.623 | 0.403 | 0.886 | 0.003 | 0.63 | 0.713 | 0.5 | 0.99 | True |
| attack | Counter-attack | severity | severe | 2423 | 2292.9 | 1.057 | 1.024 | 1.086 | 0.008 | 1.054 | 1.005 | 0.978 | 1.03 | False |
| attack | Counter-attack | pattern | impact · thigh | 79 | 46.946 | 1.683 | 1.095 | 2.166 | 0.006 | 1.679 | 1.343 | 0.917 | 1.708 | False |
| attack | Direct play | pattern | muscle · groin/adductor/hip | 462 | 519.378 | 0.89 | 0.805 | 0.976 | 0.045 | 0.887 | 0.96 | 0.876 | 1.038 | False |
| attack | Direct play | severity | severe | 3365 | 3173.267 | 1.06 | 1.03 | 1.09 | 0.003 | 1.06 | 1.013 | 0.985 | 1.043 | False |
| attack | Positional possession | severity | severe | 1825 | 2091.483 | 0.873 | 0.825 | 0.918 | 0.003 | 0.874 | 0.955 | 0.905 | 1.0 | False |
| defence | Aggressive duel press | severity | severe | 2631 | 2463.279 | 1.068 | 1.024 | 1.113 | 0.003 | 1.067 | 1.036 | 0.998 | 1.074 | False |
| defence | Aggressive duel press | type | ligament/joint | 588 | 535.859 | 1.097 | 1.014 | 1.179 | 0.034 | 1.091 | 1.065 | 0.993 | 1.137 | False |
| defence | Compact mid-block | severity | severe | 2415 | 2564.035 | 0.942 | 0.899 | 0.986 | 0.005 | 0.943 | 0.984 | 0.947 | 1.02 | False |
| defence | High press, high line | severity | severe | 2427 | 2646.446 | 0.917 | 0.874 | 0.966 | 0.003 | 0.919 | 0.976 | 0.936 | 1.016 | False |
| defence | High press, high line | location | knee | 801 | 871.282 | 0.919 | 0.864 | 0.978 | 0.041 | 0.921 | 0.968 | 0.914 | 1.02 | False |
| defence | High press, high line | pattern | ligament/joint · ankle | 161 | 128.05 | 1.257 | 1.042 | 1.459 | 0.01 | 1.252 | 1.123 | 0.977 | 1.253 | False |
| defence | Low block | pattern | muscle · groin/adductor/hip | 437 | 497.044 | 0.879 | 0.801 | 0.954 | 0.025 | 0.876 | 0.941 | 0.875 | 1.007 | False |
| defence | Low block | pattern | muscle · hamstring | 867 | 980.377 | 0.884 | 0.815 | 0.953 | 0.003 | 0.882 | 0.936 | 0.869 | 1.001 | False |
| defence | Low block | location | groin/adductor/hip | 612 | 677.926 | 0.903 | 0.832 | 0.973 | 0.024 | 0.899 | 0.948 | 0.878 | 1.014 | False |
| defence | Low block | location | hamstring | 870 | 960.976 | 0.905 | 0.844 | 0.968 | 0.006 | 0.906 | 0.948 | 0.886 | 1.01 | False |
| defence | Low block | severity | severe | 3520 | 3319.24 | 1.06 | 1.029 | 1.091 | 0.003 | 1.058 | 1.003 | 0.977 | 1.03 | False |
| defence | Low block | pattern | impact · thigh | 141 | 103.222 | 1.366 | 1.04 | 1.665 | 0.01 | 1.366 | 1.11 | 0.856 | 1.332 | False |

### All tests

| phase | style | family | category | observed | expected | ratio | low | high | q (BH) | ratio + position | ratio + position + strength | adjusted low | adjusted high | robust | p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| attack | Positional possession | type | muscle | 2320 | 2303.796 | 1.007 | 0.974 | 1.05 | 0.719 | 1.009 | 0.994 | 0.969 | 1.025 | False | 0.504 |
| attack | Positional possession | type | ligament/joint | 366 | 367.411 | 0.996 | 0.899 | 1.084 | 0.961 | 0.996 | 1.006 | 0.915 | 1.088 | False | 0.931 |
| attack | Positional possession | type | impact | 354 | 359.593 | 0.984 | 0.834 | 1.181 | 0.869 | 0.977 | 1.064 | 0.928 | 1.245 | False | 0.756 |
| attack | Positional possession | type | fracture/bone | 143 | 152.518 | 0.938 | 0.768 | 1.115 | 0.582 | 0.927 | 0.923 | 0.739 | 1.095 | False | 0.345 |
| attack | Positional possession | type | tendon | 89 | 95.158 | 0.935 | 0.678 | 1.164 | 0.697 | 0.936 | 0.973 | 0.731 | 1.187 | False | 0.478 |
| attack | Positional possession | type | other | 102 | 95.524 | 1.068 | 0.871 | 1.243 | 0.611 | 1.077 | 1.042 | 0.878 | 1.198 | False | 0.391 |
| attack | Positional possession | location | knee | 606 | 656.486 | 0.923 | 0.851 | 1.0 | 0.124 | 0.931 | 0.996 | 0.933 | 1.057 | False | 0.02 |
| attack | Positional possession | location | hamstring | 694 | 667.961 | 1.039 | 0.947 | 1.127 | 0.468 | 1.039 | 0.994 | 0.91 | 1.068 | False | 0.224 |
| attack | Positional possession | location | groin/adductor/hip | 453 | 414.987 | 1.092 | 0.989 | 1.188 | 0.132 | 1.089 | 1.006 | 0.917 | 1.092 | False | 0.027 |
| attack | Positional possession | location | ankle | 399 | 405.668 | 0.984 | 0.878 | 1.085 | 0.827 | 0.984 | 0.966 | 0.868 | 1.064 | False | 0.698 |
| attack | Positional possession | location | calf/achilles/lower leg | 391 | 373.158 | 1.048 | 0.955 | 1.139 | 0.523 | 1.046 | 1.042 | 0.958 | 1.132 | False | 0.281 |
| attack | Positional possession | location | thigh | 205 | 212.828 | 0.963 | 0.814 | 1.132 | 0.766 | 0.973 | 1.053 | 0.906 | 1.202 | False | 0.578 |
| attack | Positional possession | location | upper body | 167 | 181.73 | 0.919 | 0.797 | 1.043 | 0.382 | 0.903 | 0.959 | 0.859 | 1.075 | False | 0.169 |
| attack | Positional possession | location | foot/toe | 137 | 154.116 | 0.889 | 0.732 | 1.065 | 0.278 | 0.895 | 0.938 | 0.784 | 1.105 | False | 0.101 |
| attack | Positional possession | pattern | muscle · hamstring | 694 | 670.108 | 1.036 | 0.927 | 1.14 | 0.566 | 1.04 | 0.975 | 0.884 | 1.059 | False | 0.319 |
| attack | Positional possession | pattern | muscle · groin/adductor/hip | 334 | 298.421 | 1.119 | 0.963 | 1.264 | 0.128 | 1.115 | 0.997 | 0.882 | 1.103 | False | 0.022 |
| attack | Positional possession | pattern | muscle · calf/achilles/lower leg | 308 | 278.945 | 1.104 | 0.948 | 1.261 | 0.221 | 1.101 | 1.056 | 0.93 | 1.189 | False | 0.065 |
| attack | Positional possession | pattern | ligament/joint · knee | 204 | 207.673 | 0.982 | 0.846 | 1.097 | 0.88 | 0.987 | 0.979 | 0.839 | 1.085 | False | 0.77 |
| attack | Positional possession | pattern | muscle · thigh | 129 | 131.368 | 0.982 | 0.781 | 1.19 | 0.916 | 0.986 | 0.949 | 0.778 | 1.123 | False | 0.821 |
| attack | Positional possession | pattern | ligament/joint · ankle | 113 | 90.691 | 1.246 | 1.055 | 1.45 | 0.066 | 1.235 | 1.083 | 0.944 | 1.231 | False | 0.008 |
| attack | Positional possession | pattern | impact · thigh | 76 | 79.855 | 0.952 | 0.678 | 1.295 | 0.827 | 0.956 | 1.233 | 0.982 | 1.564 | False | 0.684 |
| attack | Positional possession | pattern | tendon · calf/achilles/lower leg | 50 | 54.333 | 0.92 | 0.544 | 1.327 | 0.732 | 0.921 | 0.903 | 0.538 | 1.271 | False | 0.517 |
| attack | Positional possession | severity | severe | 1825 | 2091.483 | 0.873 | 0.825 | 0.918 | 0.003 | 0.874 | 0.955 | 0.905 | 1.0 | False | 0.0 |
| attack | Build-up into the box | type | muscle | 3624 | 3566.722 | 1.016 | 0.992 | 1.041 | 0.221 | 1.018 | 1.007 | 0.985 | 1.029 | False | 0.065 |
| attack | Build-up into the box | type | ligament/joint | 654 | 645.97 | 1.012 | 0.927 | 1.097 | 0.827 | 1.01 | 1.039 | 0.959 | 1.118 | False | 0.701 |
| attack | Build-up into the box | type | impact | 487 | 538.008 | 0.905 | 0.78 | 1.043 | 0.132 | 0.897 | 0.926 | 0.813 | 1.054 | False | 0.026 |
| attack | Build-up into the box | type | fracture/bone | 240 | 251.274 | 0.955 | 0.849 | 1.072 | 0.611 | 0.956 | 0.973 | 0.882 | 1.071 | False | 0.392 |
| attack | Build-up into the box | type | tendon | 174 | 158.418 | 1.098 | 0.948 | 1.271 | 0.382 | 1.094 | 1.077 | 0.934 | 1.23 | False | 0.17 |
| attack | Build-up into the box | type | other | 137 | 155.607 | 0.88 | 0.726 | 1.028 | 0.219 | 0.877 | 0.884 | 0.736 | 1.02 | False | 0.06 |
| attack | Build-up into the box | location | knee | 1119 | 1116.617 | 1.002 | 0.94 | 1.069 | 0.961 | 1.0 | 1.018 | 0.964 | 1.077 | False | 0.928 |
| attack | Build-up into the box | location | hamstring | 1053 | 1038.578 | 1.014 | 0.942 | 1.091 | 0.766 | 1.017 | 1.005 | 0.94 | 1.078 | False | 0.586 |
| attack | Build-up into the box | location | groin/adductor/hip | 705 | 712.902 | 0.989 | 0.9 | 1.08 | 0.85 | 0.991 | 0.977 | 0.897 | 1.051 | False | 0.725 |
| attack | Build-up into the box | location | ankle | 738 | 693.597 | 1.064 | 0.965 | 1.157 | 0.161 | 1.059 | 1.054 | 0.97 | 1.133 | False | 0.038 |
| attack | Build-up into the box | location | calf/achilles/lower leg | 604 | 601.023 | 1.005 | 0.918 | 1.09 | 0.943 | 1.005 | 0.975 | 0.901 | 1.047 | False | 0.892 |
| attack | Build-up into the box | location | thigh | 298 | 346.332 | 0.86 | 0.724 | 1.008 | 0.051 | 0.863 | 0.893 | 0.766 | 1.037 | False | 0.005 |
| attack | Build-up into the box | location | upper body | 301 | 320.609 | 0.939 | 0.843 | 1.049 | 0.356 | 0.943 | 0.945 | 0.859 | 1.041 | False | 0.147 |
| attack | Build-up into the box | location | foot/toe | 265 | 258.571 | 1.025 | 0.916 | 1.155 | 0.783 | 1.021 | 1.033 | 0.932 | 1.152 | False | 0.622 |
| attack | Build-up into the box | pattern | muscle · hamstring | 1051 | 1016.668 | 1.034 | 0.947 | 1.128 | 0.506 | 1.036 | 1.01 | 0.933 | 1.093 | False | 0.255 |
| attack | Build-up into the box | pattern | muscle · groin/adductor/hip | 525 | 504.787 | 1.04 | 0.939 | 1.144 | 0.536 | 1.046 | 1.002 | 0.912 | 1.09 | False | 0.297 |
| attack | Build-up into the box | pattern | muscle · calf/achilles/lower leg | 437 | 434.436 | 1.006 | 0.868 | 1.155 | 0.943 | 1.008 | 0.954 | 0.835 | 1.075 | False | 0.896 |
| attack | Build-up into the box | pattern | ligament/joint · knee | 378 | 383.387 | 0.986 | 0.878 | 1.101 | 0.859 | 0.983 | 1.024 | 0.918 | 1.136 | False | 0.742 |
| attack | Build-up into the box | pattern | muscle · thigh | 221 | 218.558 | 1.011 | 0.855 | 1.167 | 0.925 | 1.011 | 0.983 | 0.854 | 1.112 | False | 0.855 |
| attack | Build-up into the box | pattern | ligament/joint · ankle | 184 | 166.817 | 1.103 | 0.922 | 1.286 | 0.315 | 1.097 | 1.046 | 0.889 | 1.198 | False | 0.122 |
| attack | Build-up into the box | pattern | impact · thigh | 77 | 123.558 | 0.623 | 0.403 | 0.886 | 0.003 | 0.63 | 0.713 | 0.5 | 0.99 | True | 0.0 |
| attack | Build-up into the box | pattern | tendon · calf/achilles/lower leg | 106 | 90.836 | 1.167 | 0.934 | 1.394 | 0.237 | 1.163 | 1.174 | 0.954 | 1.399 | False | 0.076 |
| attack | Build-up into the box | severity | severe | 3380 | 3435.35 | 0.984 | 0.948 | 1.022 | 0.425 | 0.985 | 1.01 | 0.976 | 1.045 | False | 0.196 |
| attack | Counter-attack | type | muscle | 2259 | 2316.266 | 0.975 | 0.942 | 1.004 | 0.195 | 0.974 | 0.988 | 0.958 | 1.016 | False | 0.05 |
| attack | Counter-attack | type | ligament/joint | 505 | 487.741 | 1.035 | 0.932 | 1.124 | 0.592 | 1.036 | 1.005 | 0.916 | 1.081 | False | 0.363 |
| attack | Counter-attack | type | impact | 397 | 374.356 | 1.06 | 0.878 | 1.249 | 0.52 | 1.075 | 1.047 | 0.883 | 1.203 | False | 0.277 |
| attack | Counter-attack | type | fracture/bone | 196 | 192.81 | 1.017 | 0.88 | 1.162 | 0.897 | 1.001 | 1.004 | 0.871 | 1.141 | False | 0.794 |
| attack | Counter-attack | type | tendon | 131 | 140.423 | 0.933 | 0.775 | 1.116 | 0.632 | 0.934 | 0.918 | 0.776 | 1.061 | False | 0.419 |
| attack | Counter-attack | type | other | 132 | 108.404 | 1.218 | 1.002 | 1.435 | 0.072 | 1.223 | 1.158 | 0.971 | 1.353 | False | 0.009 |
| attack | Counter-attack | location | knee | 822 | 793.369 | 1.036 | 0.968 | 1.105 | 0.5 | 1.033 | 0.999 | 0.934 | 1.056 | False | 0.247 |
| attack | Counter-attack | location | hamstring | 629 | 649.823 | 0.968 | 0.883 | 1.051 | 0.606 | 0.965 | 1.004 | 0.929 | 1.076 | False | 0.379 |
| attack | Counter-attack | location | groin/adductor/hip | 491 | 485.22 | 1.012 | 0.929 | 1.093 | 0.881 | 1.011 | 1.034 | 0.959 | 1.109 | False | 0.776 |
| attack | Counter-attack | location | ankle | 433 | 451.068 | 0.96 | 0.843 | 1.07 | 0.582 | 0.963 | 0.979 | 0.871 | 1.078 | False | 0.341 |
| attack | Counter-attack | location | calf/achilles/lower leg | 337 | 379.719 | 0.887 | 0.791 | 0.989 | 0.128 | 0.891 | 0.923 | 0.825 | 1.014 | False | 0.023 |
| attack | Counter-attack | location | thigh | 232 | 199.822 | 1.161 | 0.981 | 1.333 | 0.128 | 1.153 | 1.09 | 0.943 | 1.23 | False | 0.022 |
| attack | Counter-attack | location | upper body | 246 | 232.052 | 1.06 | 0.927 | 1.21 | 0.519 | 1.072 | 1.058 | 0.938 | 1.187 | False | 0.271 |
| attack | Counter-attack | location | foot/toe | 190 | 187.528 | 1.013 | 0.876 | 1.145 | 0.92 | 1.011 | 0.958 | 0.832 | 1.072 | False | 0.84 |
| attack | Counter-attack | pattern | muscle · hamstring | 627 | 641.55 | 0.977 | 0.881 | 1.071 | 0.766 | 0.972 | 1.023 | 0.941 | 1.105 | False | 0.586 |
| attack | Counter-attack | pattern | muscle · groin/adductor/hip | 355 | 353.414 | 1.004 | 0.909 | 1.107 | 0.961 | 1.004 | 1.057 | 0.965 | 1.15 | False | 0.935 |
| attack | Counter-attack | pattern | muscle · calf/achilles/lower leg | 219 | 249.885 | 0.876 | 0.739 | 1.017 | 0.221 | 0.884 | 0.947 | 0.821 | 1.076 | False | 0.062 |
| attack | Counter-attack | pattern | ligament/joint · knee | 303 | 275.951 | 1.098 | 0.968 | 1.233 | 0.228 | 1.094 | 1.068 | 0.959 | 1.183 | False | 0.072 |
| attack | Counter-attack | pattern | muscle · thigh | 151 | 148.764 | 1.015 | 0.851 | 1.196 | 0.924 | 1.011 | 1.018 | 0.856 | 1.19 | False | 0.848 |
| attack | Counter-attack | pattern | ligament/joint · ankle | 116 | 127.217 | 0.912 | 0.749 | 1.064 | 0.509 | 0.911 | 0.974 | 0.809 | 1.128 | False | 0.26 |
| attack | Counter-attack | pattern | impact · thigh | 79 | 46.946 | 1.683 | 1.095 | 2.166 | 0.006 | 1.679 | 1.343 | 0.917 | 1.708 | False | 0.0 |
| attack | Counter-attack | pattern | tendon · calf/achilles/lower leg | 76 | 83.217 | 0.913 | 0.702 | 1.13 | 0.632 | 0.915 | 0.884 | 0.695 | 1.075 | False | 0.418 |
| attack | Counter-attack | severity | severe | 2423 | 2292.9 | 1.057 | 1.024 | 1.086 | 0.008 | 1.054 | 1.005 | 0.978 | 1.03 | False | 0.0 |
| attack | Direct play | type | muscle | 3213 | 3229.215 | 0.995 | 0.968 | 1.021 | 0.779 | 0.993 | 1.004 | 0.979 | 1.028 | False | 0.611 |
| attack | Direct play | type | ligament/joint | 609 | 632.878 | 0.962 | 0.89 | 1.028 | 0.5 | 0.964 | 0.955 | 0.882 | 1.023 | False | 0.245 |
| attack | Direct play | type | impact | 564 | 530.044 | 1.064 | 0.969 | 1.16 | 0.343 | 1.068 | 0.999 | 0.916 | 1.083 | False | 0.137 |
| attack | Direct play | type | fracture/bone | 264 | 246.398 | 1.071 | 0.935 | 1.21 | 0.403 | 1.092 | 1.071 | 0.945 | 1.204 | False | 0.182 |
| attack | Direct play | type | tendon | 166 | 166.001 | 1.0 | 0.835 | 1.174 | 1.0 | 1.003 | 1.011 | 0.856 | 1.162 | False | 1.0 |
| attack | Direct play | type | other | 157 | 168.465 | 0.932 | 0.786 | 1.076 | 0.506 | 0.928 | 0.974 | 0.828 | 1.119 | False | 0.256 |
| attack | Direct play | location | knee | 1077 | 1057.528 | 1.018 | 0.957 | 1.081 | 0.686 | 1.018 | 0.985 | 0.93 | 1.043 | False | 0.466 |
| attack | Direct play | location | hamstring | 873 | 892.638 | 0.978 | 0.893 | 1.066 | 0.672 | 0.977 | 0.996 | 0.926 | 1.065 | False | 0.453 |
| attack | Direct play | location | groin/adductor/hip | 656 | 691.892 | 0.948 | 0.878 | 1.024 | 0.279 | 0.948 | 0.996 | 0.934 | 1.063 | False | 0.104 |
| attack | Direct play | location | ankle | 585 | 604.667 | 0.967 | 0.897 | 1.041 | 0.585 | 0.97 | 0.976 | 0.905 | 1.048 | False | 0.35 |
| attack | Direct play | location | calf/achilles/lower leg | 550 | 528.1 | 1.041 | 0.94 | 1.142 | 0.525 | 1.04 | 1.053 | 0.959 | 1.144 | False | 0.285 |
| attack | Direct play | location | thigh | 334 | 310.019 | 1.077 | 0.928 | 1.225 | 0.362 | 1.071 | 1.019 | 0.888 | 1.148 | False | 0.152 |
| attack | Direct play | location | upper body | 309 | 288.609 | 1.071 | 0.961 | 1.18 | 0.343 | 1.068 | 1.038 | 0.947 | 1.142 | False | 0.14 |
| attack | Direct play | location | foot/toe | 245 | 236.785 | 1.035 | 0.911 | 1.159 | 0.741 | 1.036 | 1.038 | 0.923 | 1.153 | False | 0.53 |
| attack | Direct play | pattern | muscle · hamstring | 872 | 915.674 | 0.952 | 0.857 | 1.053 | 0.343 | 0.951 | 0.993 | 0.917 | 1.069 | False | 0.138 |
| attack | Direct play | pattern | muscle · groin/adductor/hip | 462 | 519.378 | 0.89 | 0.805 | 0.976 | 0.045 | 0.887 | 0.96 | 0.876 | 1.038 | False | 0.004 |
| attack | Direct play | pattern | muscle · calf/achilles/lower leg | 386 | 386.734 | 0.998 | 0.874 | 1.121 | 0.978 | 0.993 | 1.046 | 0.929 | 1.152 | False | 0.967 |
| attack | Direct play | pattern | ligament/joint · knee | 357 | 374.989 | 0.952 | 0.853 | 1.047 | 0.52 | 0.955 | 0.937 | 0.835 | 1.032 | False | 0.275 |
| attack | Direct play | pattern | muscle · thigh | 222 | 224.31 | 0.99 | 0.859 | 1.116 | 0.928 | 0.99 | 1.038 | 0.907 | 1.165 | False | 0.865 |
| attack | Direct play | pattern | ligament/joint · ankle | 153 | 181.274 | 0.844 | 0.703 | 0.988 | 0.087 | 0.852 | 0.918 | 0.776 | 1.06 | False | 0.011 |
| attack | Direct play | pattern | impact · thigh | 110 | 91.641 | 1.2 | 0.898 | 1.556 | 0.249 | 1.181 | 0.969 | 0.749 | 1.222 | False | 0.081 |
| attack | Direct play | pattern | tendon · calf/achilles/lower leg | 94 | 97.615 | 0.963 | 0.74 | 1.189 | 0.827 | 0.964 | 0.997 | 0.786 | 1.212 | False | 0.702 |
| attack | Direct play | severity | severe | 3365 | 3173.267 | 1.06 | 1.03 | 1.09 | 0.003 | 1.06 | 1.013 | 0.985 | 1.043 | False | 0.0 |
| defence | High press, high line | type | muscle | 2715 | 2666.953 | 1.018 | 0.988 | 1.052 | 0.252 | 1.02 | 1.003 | 0.979 | 1.025 | False | 0.084 |
| defence | High press, high line | type | ligament/joint | 489 | 500.258 | 0.977 | 0.903 | 1.048 | 0.741 | 0.981 | 1.0 | 0.927 | 1.067 | False | 0.536 |
| defence | High press, high line | type | impact | 477 | 493.868 | 0.966 | 0.868 | 1.083 | 0.638 | 0.955 | 1.011 | 0.919 | 1.114 | False | 0.427 |
| defence | High press, high line | type | fracture/bone | 182 | 196.001 | 0.929 | 0.794 | 1.058 | 0.479 | 0.92 | 0.907 | 0.773 | 1.053 | False | 0.232 |
| defence | High press, high line | type | tendon | 133 | 137.04 | 0.971 | 0.782 | 1.165 | 0.827 | 0.966 | 1.037 | 0.863 | 1.228 | False | 0.7 |
| defence | High press, high line | type | other | 114 | 115.88 | 0.984 | 0.806 | 1.134 | 0.918 | 0.991 | 1.018 | 0.847 | 1.16 | False | 0.829 |
| defence | High press, high line | location | knee | 801 | 871.282 | 0.919 | 0.864 | 0.978 | 0.041 | 0.921 | 0.968 | 0.914 | 1.02 | False | 0.004 |
| defence | High press, high line | location | hamstring | 814 | 771.716 | 1.055 | 0.967 | 1.142 | 0.226 | 1.058 | 1.005 | 0.925 | 1.08 | False | 0.068 |
| defence | High press, high line | location | groin/adductor/hip | 600 | 560.978 | 1.07 | 0.993 | 1.148 | 0.19 | 1.069 | 1.035 | 0.97 | 1.103 | False | 0.048 |
| defence | High press, high line | location | ankle | 564 | 528.635 | 1.067 | 0.965 | 1.176 | 0.221 | 1.063 | 1.026 | 0.93 | 1.129 | False | 0.064 |
| defence | High press, high line | location | calf/achilles/lower leg | 418 | 438.307 | 0.954 | 0.842 | 1.059 | 0.511 | 0.95 | 0.967 | 0.871 | 1.063 | False | 0.264 |
| defence | High press, high line | location | thigh | 270 | 263.588 | 1.024 | 0.853 | 1.197 | 0.827 | 1.033 | 1.099 | 0.938 | 1.251 | False | 0.676 |
| defence | High press, high line | location | upper body | 242 | 247.12 | 0.979 | 0.875 | 1.082 | 0.827 | 0.979 | 0.966 | 0.874 | 1.06 | False | 0.677 |
| defence | High press, high line | location | foot/toe | 177 | 206.875 | 0.856 | 0.738 | 0.984 | 0.093 | 0.857 | 0.903 | 0.786 | 1.03 | False | 0.013 |
| defence | High press, high line | pattern | muscle · hamstring | 814 | 771.287 | 1.055 | 0.964 | 1.147 | 0.272 | 1.062 | 1.003 | 0.921 | 1.084 | False | 0.096 |
| defence | High press, high line | pattern | muscle · groin/adductor/hip | 446 | 403.061 | 1.107 | 0.996 | 1.223 | 0.091 | 1.106 | 1.053 | 0.96 | 1.146 | False | 0.012 |
| defence | High press, high line | pattern | muscle · calf/achilles/lower leg | 292 | 308.113 | 0.948 | 0.809 | 1.095 | 0.566 | 0.947 | 0.937 | 0.813 | 1.056 | False | 0.321 |
| defence | High press, high line | pattern | ligament/joint · knee | 249 | 281.567 | 0.884 | 0.786 | 0.985 | 0.128 | 0.888 | 0.927 | 0.835 | 1.017 | False | 0.023 |
| defence | High press, high line | pattern | muscle · thigh | 187 | 167.254 | 1.118 | 0.913 | 1.318 | 0.265 | 1.126 | 1.087 | 0.915 | 1.249 | False | 0.091 |
| defence | High press, high line | pattern | ligament/joint · ankle | 161 | 128.05 | 1.257 | 1.042 | 1.459 | 0.01 | 1.252 | 1.123 | 0.977 | 1.253 | False | 0.001 |
| defence | High press, high line | pattern | impact · thigh | 82 | 95.27 | 0.861 | 0.581 | 1.211 | 0.425 | 0.865 | 1.114 | 0.822 | 1.36 | False | 0.194 |
| defence | High press, high line | pattern | tendon · calf/achilles/lower leg | 81 | 80.103 | 1.011 | 0.726 | 1.37 | 0.953 | 0.999 | 1.078 | 0.799 | 1.416 | False | 0.912 |
| defence | High press, high line | severity | severe | 2427 | 2646.446 | 0.917 | 0.874 | 0.966 | 0.003 | 0.919 | 0.976 | 0.936 | 1.016 | False | 0.0 |
| defence | Compact mid-block | type | muscle | 2901 | 2852.894 | 1.017 | 0.987 | 1.048 | 0.278 | 1.018 | 1.013 | 0.984 | 1.043 | False | 0.101 |
| defence | Compact mid-block | type | ligament/joint | 507 | 531.351 | 0.954 | 0.846 | 1.059 | 0.427 | 0.953 | 0.968 | 0.872 | 1.065 | False | 0.2 |
| defence | Compact mid-block | type | impact | 432 | 432.566 | 0.999 | 0.836 | 1.188 | 0.985 | 0.998 | 1.001 | 0.862 | 1.163 | False | 0.98 |
| defence | Compact mid-block | type | fracture/bone | 204 | 202.263 | 1.009 | 0.873 | 1.145 | 0.937 | 1.005 | 1.057 | 0.929 | 1.179 | False | 0.881 |
| defence | Compact mid-block | type | tendon | 105 | 130.446 | 0.805 | 0.646 | 0.97 | 0.101 | 0.799 | 0.794 | 0.64 | 0.942 | True | 0.015 |
| defence | Compact mid-block | type | other | 141 | 140.48 | 1.004 | 0.829 | 1.176 | 0.977 | 0.999 | 0.966 | 0.808 | 1.127 | False | 0.956 |
| defence | Compact mid-block | location | knee | 822 | 853.035 | 0.964 | 0.889 | 1.042 | 0.452 | 0.963 | 0.981 | 0.913 | 1.045 | False | 0.214 |
| defence | Compact mid-block | location | hamstring | 817 | 782.566 | 1.044 | 0.974 | 1.123 | 0.376 | 1.044 | 1.039 | 0.97 | 1.118 | False | 0.16 |
| defence | Compact mid-block | location | groin/adductor/hip | 610 | 565.923 | 1.078 | 0.972 | 1.172 | 0.144 | 1.081 | 1.02 | 0.94 | 1.098 | False | 0.032 |
| defence | Compact mid-block | location | ankle | 502 | 513.136 | 0.978 | 0.892 | 1.068 | 0.757 | 0.975 | 0.981 | 0.897 | 1.063 | False | 0.556 |
| defence | Compact mid-block | location | calf/achilles/lower leg | 446 | 463.326 | 0.963 | 0.831 | 1.073 | 0.592 | 0.961 | 0.955 | 0.843 | 1.049 | False | 0.361 |
| defence | Compact mid-block | location | thigh | 274 | 283.677 | 0.966 | 0.817 | 1.142 | 0.756 | 0.97 | 0.979 | 0.84 | 1.139 | False | 0.55 |
| defence | Compact mid-block | location | upper body | 219 | 230.783 | 0.949 | 0.829 | 1.091 | 0.582 | 0.95 | 1.013 | 0.902 | 1.123 | False | 0.336 |
| defence | Compact mid-block | location | foot/toe | 190 | 192.387 | 0.988 | 0.83 | 1.152 | 0.92 | 0.987 | 1.013 | 0.864 | 1.153 | False | 0.837 |
| defence | Compact mid-block | pattern | muscle · hamstring | 816 | 761.394 | 1.072 | 0.972 | 1.184 | 0.198 | 1.072 | 1.046 | 0.952 | 1.149 | False | 0.052 |
| defence | Compact mid-block | pattern | muscle · groin/adductor/hip | 441 | 397.937 | 1.108 | 0.963 | 1.242 | 0.101 | 1.108 | 1.023 | 0.92 | 1.112 | False | 0.015 |
| defence | Compact mid-block | pattern | muscle · calf/achilles/lower leg | 341 | 326.201 | 1.045 | 0.869 | 1.199 | 0.624 | 1.04 | 1.004 | 0.858 | 1.127 | False | 0.404 |
| defence | Compact mid-block | pattern | ligament/joint · knee | 312 | 298.043 | 1.047 | 0.922 | 1.183 | 0.592 | 1.045 | 1.04 | 0.932 | 1.164 | False | 0.357 |
| defence | Compact mid-block | pattern | muscle · thigh | 174 | 171.966 | 1.012 | 0.849 | 1.174 | 0.928 | 1.021 | 0.996 | 0.84 | 1.157 | False | 0.868 |
| defence | Compact mid-block | pattern | ligament/joint · ankle | 131 | 145.312 | 0.902 | 0.714 | 1.075 | 0.376 | 0.895 | 0.875 | 0.691 | 1.048 | False | 0.163 |
| defence | Compact mid-block | pattern | impact · thigh | 100 | 105.964 | 0.944 | 0.706 | 1.287 | 0.779 | 0.946 | 0.967 | 0.765 | 1.224 | False | 0.611 |
| defence | Compact mid-block | pattern | tendon · calf/achilles/lower leg | 59 | 70.778 | 0.834 | 0.59 | 1.088 | 0.343 | 0.838 | 0.799 | 0.564 | 1.029 | False | 0.137 |
| defence | Compact mid-block | severity | severe | 2415 | 2564.035 | 0.942 | 0.899 | 0.986 | 0.005 | 0.943 | 0.984 | 0.947 | 1.02 | False | 0.0 |
| defence | Aggressive duel press | type | muscle | 2702 | 2741.575 | 0.986 | 0.961 | 1.014 | 0.279 | 0.985 | 0.989 | 0.966 | 1.014 | False | 0.105 |
| defence | Aggressive duel press | type | ligament/joint | 588 | 535.859 | 1.097 | 1.014 | 1.179 | 0.034 | 1.091 | 1.065 | 0.993 | 1.137 | False | 0.003 |
| defence | Aggressive duel press | type | impact | 279 | 311.634 | 0.895 | 0.744 | 1.061 | 0.161 | 0.897 | 0.918 | 0.765 | 1.084 | False | 0.038 |
| defence | Aggressive duel press | type | fracture/bone | 222 | 216.494 | 1.025 | 0.905 | 1.154 | 0.779 | 1.033 | 1.006 | 0.886 | 1.125 | False | 0.614 |
| defence | Aggressive duel press | type | tendon | 158 | 152.344 | 1.037 | 0.84 | 1.228 | 0.766 | 1.054 | 1.077 | 0.893 | 1.249 | False | 0.575 |
| defence | Aggressive duel press | type | other | 144 | 135.096 | 1.066 | 0.906 | 1.22 | 0.533 | 1.073 | 1.046 | 0.904 | 1.178 | False | 0.292 |
| defence | Aggressive duel press | location | knee | 877 | 828.775 | 1.058 | 0.984 | 1.137 | 0.132 | 1.06 | 1.029 | 0.963 | 1.096 | False | 0.026 |
| defence | Aggressive duel press | location | hamstring | 748 | 733.741 | 1.019 | 0.908 | 1.127 | 0.719 | 1.015 | 1.018 | 0.927 | 1.104 | False | 0.502 |
| defence | Aggressive duel press | location | groin/adductor/hip | 483 | 500.173 | 0.966 | 0.883 | 1.057 | 0.566 | 0.968 | 1.002 | 0.927 | 1.082 | False | 0.323 |
| defence | Aggressive duel press | location | ankle | 437 | 442.746 | 0.987 | 0.879 | 1.081 | 0.854 | 0.986 | 0.993 | 0.894 | 1.083 | False | 0.734 |
| defence | Aggressive duel press | location | calf/achilles/lower leg | 425 | 420.963 | 1.01 | 0.923 | 1.097 | 0.904 | 1.01 | 1.026 | 0.952 | 1.099 | False | 0.805 |
| defence | Aggressive duel press | location | thigh | 172 | 204.93 | 0.839 | 0.672 | 1.018 | 0.066 | 0.835 | 0.851 | 0.694 | 1.011 | False | 0.008 |
| defence | Aggressive duel press | location | upper body | 232 | 238.841 | 0.971 | 0.847 | 1.103 | 0.741 | 0.966 | 0.947 | 0.835 | 1.066 | False | 0.533 |
| defence | Aggressive duel press | location | foot/toe | 195 | 185.271 | 1.053 | 0.888 | 1.216 | 0.582 | 1.061 | 1.018 | 0.865 | 1.169 | False | 0.343 |
| defence | Aggressive duel press | pattern | muscle · hamstring | 747 | 730.942 | 1.022 | 0.892 | 1.149 | 0.719 | 1.018 | 1.029 | 0.919 | 1.14 | False | 0.504 |
| defence | Aggressive duel press | pattern | muscle · groin/adductor/hip | 352 | 377.959 | 0.931 | 0.834 | 1.033 | 0.265 | 0.937 | 0.985 | 0.893 | 1.083 | False | 0.092 |
| defence | Aggressive duel press | pattern | muscle · calf/achilles/lower leg | 275 | 281.363 | 0.977 | 0.86 | 1.088 | 0.827 | 0.976 | 1.009 | 0.893 | 1.129 | False | 0.677 |
| defence | Aggressive duel press | pattern | ligament/joint · knee | 341 | 313.529 | 1.088 | 0.962 | 1.214 | 0.173 | 1.082 | 1.052 | 0.948 | 1.163 | False | 0.042 |
| defence | Aggressive duel press | pattern | muscle · thigh | 150 | 166.363 | 0.902 | 0.753 | 1.06 | 0.279 | 0.895 | 0.926 | 0.782 | 1.077 | False | 0.106 |
| defence | Aggressive duel press | pattern | ligament/joint · ankle | 151 | 146.207 | 1.033 | 0.825 | 1.223 | 0.778 | 1.031 | 1.072 | 0.889 | 1.238 | False | 0.601 |
| defence | Aggressive duel press | pattern | impact · thigh | 19 | 37.544 | 0.506 | 0.303 | 1.002 | 0.066 | 0.497 | 0.501 | 0.306 | 0.904 | True | 0.008 |
| defence | Aggressive duel press | pattern | tendon · calf/achilles/lower leg | 92 | 92.309 | 0.997 | 0.752 | 1.21 | 0.978 | 1.007 | 1.055 | 0.824 | 1.24 | False | 0.967 |
| defence | Aggressive duel press | severity | severe | 2631 | 2463.279 | 1.068 | 1.024 | 1.113 | 0.003 | 1.067 | 1.036 | 0.998 | 1.074 | False | 0.0 |
| defence | Low block | type | muscle | 3098 | 3154.579 | 0.982 | 0.953 | 1.007 | 0.208 | 0.98 | 0.995 | 0.97 | 1.016 | False | 0.055 |
| defence | Low block | type | ligament/joint | 550 | 566.532 | 0.971 | 0.874 | 1.054 | 0.611 | 0.974 | 0.967 | 0.879 | 1.045 | False | 0.387 |
| defence | Low block | type | impact | 614 | 563.932 | 1.089 | 0.979 | 1.221 | 0.132 | 1.099 | 1.032 | 0.948 | 1.136 | False | 0.026 |
| defence | Low block | type | fracture/bone | 235 | 228.243 | 1.03 | 0.911 | 1.168 | 0.766 | 1.034 | 1.028 | 0.924 | 1.149 | False | 0.587 |
| defence | Low block | type | tendon | 164 | 140.17 | 1.17 | 0.991 | 1.383 | 0.132 | 1.163 | 1.074 | 0.922 | 1.263 | False | 0.028 |
| defence | Low block | type | other | 129 | 136.545 | 0.945 | 0.775 | 1.133 | 0.632 | 0.937 | 0.974 | 0.802 | 1.155 | False | 0.419 |
| defence | Low block | location | knee | 1124 | 1070.908 | 1.05 | 0.984 | 1.113 | 0.156 | 1.048 | 1.016 | 0.961 | 1.07 | False | 0.035 |
| defence | Low block | location | hamstring | 870 | 960.976 | 0.905 | 0.844 | 0.968 | 0.006 | 0.906 | 0.948 | 0.886 | 1.01 | False | 0.0 |
| defence | Low block | location | groin/adductor/hip | 612 | 677.926 | 0.903 | 0.832 | 0.973 | 0.024 | 0.899 | 0.948 | 0.878 | 1.014 | False | 0.002 |
| defence | Low block | location | ankle | 652 | 670.483 | 0.972 | 0.896 | 1.046 | 0.604 | 0.978 | 0.998 | 0.921 | 1.07 | False | 0.374 |
| defence | Low block | location | calf/achilles/lower leg | 593 | 559.403 | 1.06 | 0.973 | 1.152 | 0.265 | 1.064 | 1.043 | 0.964 | 1.123 | False | 0.091 |
| defence | Low block | location | thigh | 353 | 316.806 | 1.114 | 0.964 | 1.254 | 0.144 | 1.106 | 1.034 | 0.922 | 1.146 | False | 0.032 |
| defence | Low block | location | upper body | 330 | 306.256 | 1.078 | 0.972 | 1.191 | 0.228 | 1.081 | 1.06 | 0.97 | 1.16 | False | 0.071 |
| defence | Low block | location | foot/toe | 275 | 252.467 | 1.089 | 0.967 | 1.221 | 0.228 | 1.082 | 1.051 | 0.942 | 1.162 | False | 0.071 |
| defence | Low block | pattern | muscle · hamstring | 867 | 980.377 | 0.884 | 0.815 | 0.953 | 0.003 | 0.882 | 0.936 | 0.869 | 1.001 | False | 0.0 |
| defence | Low block | pattern | muscle · groin/adductor/hip | 437 | 497.044 | 0.879 | 0.801 | 0.954 | 0.025 | 0.876 | 0.941 | 0.875 | 1.007 | False | 0.002 |
| defence | Low block | pattern | muscle · calf/achilles/lower leg | 442 | 434.322 | 1.018 | 0.897 | 1.137 | 0.827 | 1.023 | 1.037 | 0.933 | 1.141 | False | 0.685 |
| defence | Low block | pattern | ligament/joint · knee | 340 | 348.861 | 0.975 | 0.849 | 1.09 | 0.766 | 0.977 | 0.974 | 0.851 | 1.087 | False | 0.572 |
| defence | Low block | pattern | muscle · thigh | 212 | 217.417 | 0.975 | 0.812 | 1.125 | 0.827 | 0.968 | 0.989 | 0.842 | 1.128 | False | 0.685 |
| defence | Low block | pattern | ligament/joint · ankle | 123 | 146.431 | 0.84 | 0.685 | 0.981 | 0.128 | 0.851 | 0.932 | 0.793 | 1.061 | False | 0.024 |
| defence | Low block | pattern | impact · thigh | 141 | 103.222 | 1.366 | 1.04 | 1.665 | 0.01 | 1.366 | 1.11 | 0.856 | 1.332 | False | 0.001 |
| defence | Low block | pattern | tendon · calf/achilles/lower leg | 94 | 82.81 | 1.135 | 0.888 | 1.42 | 0.376 | 1.131 | 1.047 | 0.826 | 1.327 | False | 0.163 |
| defence | Low block | severity | severe | 3520 | 3319.24 | 1.06 | 1.029 | 1.091 | 0.003 | 1.058 | 1.003 | 0.977 | 1.03 | False | 0.0 |

## 4. Clustering team-seasons by injury profile

1023 team-seasons with at least 10 injuries; features: smoothed deviation from the league-season mix (α = 10), standardised.

| k | inertia | silhouette | null silhouette (mean) | null silhouette (95th pct) | stability (mean ARI) | min cluster Jaccard | smallest cluster | above null | usable |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 10798.525 | 0.117 | 0.068 | 0.077 | 0.8 | 0.886 | 432 | True | True |
| 3 | 10010.215 | 0.103 | 0.067 | 0.072 | 0.638 | 0.632 | 309 | True | True |
| 4 | 9379.372 | 0.104 | 0.065 | 0.07 | 0.622 | 0.625 | 179 | True | True |
| 5 | 8888.253 | 0.099 | 0.068 | 0.072 | 0.506 | 0.491 | 130 | True | False |
| 6 | 8450.461 | 0.102 | 0.069 | 0.073 | 0.522 | 0.505 | 115 | True | False |
| 7 | 8109.231 | 0.102 | 0.071 | 0.076 | 0.524 | 0.402 | 99 | True | False |
| 8 | 7802.134 | 0.101 | 0.071 | 0.077 | 0.532 | 0.478 | 89 | True | False |

![k](figures/06_profile_k.png)

Group centres (z):

| index | muscle | ligament/joint | impact | fracture/bone | tendon | knee | hamstring | groin/adductor/hip | ankle | calf/achilles/lower leg | thigh | severe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1: more muscle, less ligament/joint | 0.58 | -0.47 | -0.24 | -0.11 | -0.09 | -0.43 | 0.28 | 0.23 | -0.19 | 0.16 | 0.04 | -0.2 |
| P2: more ligament/joint & more knee, less muscle | -0.79 | 0.64 | 0.33 | 0.16 | 0.12 | 0.58 | -0.38 | -0.31 | 0.26 | -0.22 | -0.05 | 0.27 |

| group | team-seasons |
|---|---|
| P1: more muscle, less ligament/joint | 591 |
| P2: more ligament/joint & more knee, less muscle | 432 |

## 5. Do the groups line up with styles?

| compared with | Cramér's V | ARI | permutation p | permutation p (within strength) |
|---|---|---|---|---|
| attack style | 0.0745 | 0.0003 | 0.1139 | 0.4372 |
| defence style | 0.1061 | 0.0026 | 0.0049 | 0.0699 |
| strength | 0.099 | 0.0065 | nan | nan |
| league | 0.0416 | -0.0007 | nan | nan |
| era | 0.0537 | 0.0004 | nan | nan |

Share of each attack style in each group (%):

| group | Positional possession | Build-up into the box | Counter-attack | Direct play |
|---|---|---|---|---|
| P1: more muscle, less ligament/joint | 64.0 | 58.0 | 52.0 | 58.0 |
| P2: more ligament/joint & more knee, less muscle | 36.0 | 42.0 | 48.0 | 42.0 |

Share of each defence style in each group (%):

| group | High press, high line | Compact mid-block | Aggressive duel press | Low block |
|---|---|---|---|---|
| P1: more muscle, less ligament/joint | 65.0 | 62.0 | 52.0 | 54.0 |
| P2: more ligament/joint & more knee, less muscle | 35.0 | 38.0 | 48.0 | 46.0 |

![Groups](figures/06_profile_clusters.png)

## 6. Outputs

- `data/06_injury_profiles/tables/`: omnibus tests, profile ratios, k selection, group centres, associations.
- `data/06_injury_profiles/team_season_profiles.parquet`: each team-season's injury-profile group.
