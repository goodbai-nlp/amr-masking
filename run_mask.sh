export masking_method=node #node, subtree
export percentage=30
export cate=dev #train, dev, test
export corpus=LDC2020


OutPath=masked_datasets/${corpus}/${masking_method}_${percentage}
if [ ! -d ${OutPath} ];then
mkdir -p ${OutPath}
fi
echo "Processing ${cate}..."
if [ "$cate" == "train" ]; then
    cate2="training"
elif [ "$cate" == "val" ]; then
    cate2="dev"
else
    cate2=$cate
fi
python3 -u load_and_mask.py --config config-default.yaml --input_file datasets/${corpus}/amrs/split/${cate2}/*-all.txt --output_prefix ${OutPath}/${cate} --mask_method $masking_method --pct $percentage

# nohup python3 -u load_and_mask.py --config config-default.yaml --input_file datasets/${corpus}/amrs/split/${cate2}/*-all.txt --output_prefix ${OutPath}/${cate}.${masking_method}_${percentage} --mask_method $masking_method --pct $percentage > logs/${corpus}/${cate}_${masking_method}_${percentage}.log &


# for corpus in LDC2017 LDC2020
# do
#     OutPath=masked_datasets/${corpus}
#     if [ ! -d ${OutPath} ];then
#     mkdir -p ${OutPath}
#     fi
#     for cate in train val test 
#     do
#         echo "Processing ${cate}..."
#         if [ "$cate" == "train" ]; then
#             cate2="training"
#         elif [ "$cate" == "val" ]; then
#             cate2="dev"
#         else
#             cate2=$cate
#         fi
#         python load_and_mask.py --config config-default.yaml --input_file datasets/${corpus}/amrs/split/${cate2}/*-all.txt --output_prefix ${OutPath}/${cate}.${masking_method}_${percentage} --mask_method $masking_method --pct $percentage
#     done
# done
