## logs
- 2024.06.05-0 初始化3DGS
- 2024.06.06-0 复现VastGaussian 
- 2024.06.06-1 调整代码 

## Scripts

export CUDA_VISIBLE_DEVICES=1

export CUDA_VISIBLE_DEVICES=0

### Local Train

```bash
python vast_train.py -s data/rubble/ -m data/rubble/output --resolution 4  -w
```