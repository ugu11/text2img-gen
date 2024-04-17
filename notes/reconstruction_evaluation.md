| Image size | Model | LPIPS &darr; |   SSIM  &uarr;  |  PSNR &uarr; |  FID &darr; | LPIPS (AlexNet) &darr; |
|------------|-------|--------------|-----------------|--------------|-------------|------------------------|
|   $128^2$  |  VAE  |  0.17        |   0.68          |  21.59       | 12.24       | 0.075                  |
|   $128^2$  |  CDD  |  0.17        |   0.67          |  21.25       | 8.99        | 0.073                  |
|   $256^2$  |  VAE  |  __0.15__    |   0.71          |  22.96       | 4.79        | 0.0685                 |
|   $256^2$  |  CDD  |  0.16        |   0.70          |  22.89       | 4.56        |
|   $512^2$  |  VAE  |  0.16        |   __0.74__      |  24.33       | 2.90        | 0.070                  |
|   $512^2$  |  CDD  |  0.17        |   0.73          |  __24.99__   | __2.78__    | 0.070                 |
|------------|-------|--------------|-----------------|--------------|-------------|
|   Mean     |  VAE  |  __0.16__    |   __0.71__      |  22.96       | 6.65        |
|   Mean     |  CDD  |  __0.16__    |   0.70          | __23.04__    | __5.44__    |
