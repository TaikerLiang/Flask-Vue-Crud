# -t: options, prd/eval/dev
# ex: sh deploy -t prd

while getopts t: flag
do
    case "${flag}" in
        t) target=${OPTARG};;
    esac
done

cd .. && python -m pytest test/ --disable-warnings
existed=$?
cd src

if [ $existed = 1 ]
then
    exit 0
fi

if [ "x$target" = "xprd" ]; then
    echo "deploy to scrapy cloud project: 407697 & 572059"
    shub image build 407697 -f ../docker/zyte/Dockerfile -b EDI_ENGINE_BASE_URL=https://master.edi.hardcoretech.co/api/ -b EDI_ENGINE_USER=tracking-local -b EDI_ENGINE_TOKEN=LK1YG0FD70TPKCG76RMSCO9HLMK7J23R5ZEJX1VM3607 -b EDI_HOST=master.edi.hardcoretech.co
    shub image push 407697
    shub image deploy 407697
    shub image build 572059 -f ../docker/zyte/Dockerfile -b EDI_ENGINE_BASE_URL=https://master.edi.hardcoretech.co/api/ -b EDI_ENGINE_USER=tracking-local -b EDI_ENGINE_TOKEN=LK1YG0FD70TPKCG76RMSCO9HLMK7J23R5ZEJX1VM3607 -b EDI_HOST=master.edi.hardcoretech.co
    shub image push 572059
    shub image deploy 572059
elif [ "x$target" = "xeval" ]; then
    echo "deploy to scrapy cloud project: 407696"
    shub image build 407696 -f ../docker/zyte/Dockerfile -b EDI_ENGINE_BASE_URL=https://eval.edi.hardcoretech.co/api/ -b EDI_ENGINE_USER=tracking-local -b EDI_ENGINE_TOKEN=TRIJRUB6Q9CYG7299OJW25A6QYPB48NKJGJF7GHN8OJU -b EDI_HOST=eval.edi.hardcoretech.co
    shub image push 407696
    shub image deploy 407696
elif [ "x$target" = "xqa" ]; then
    echo "deploy to scrapy cloud project: 544508"
    shub image build 544508 -f ../docker/zyte/Dockerfile -b EDI_ENGINE_BASE_URL=http://tracking.hardcoretech.co:18110/api/ -b EDI_ENGINE_USER=tracking-local -b EDI_ENGINE_TOKEN=LK1YG0FD70TPKCG76RMSCO9HLMK7J23R5ZEJX1VM3607 -b EDI_HOST=tracking.hardcoretech.co
    shub image push 544508
    shub image deploy 544508
elif [ "x$target" = "xdev" ]; then
    echo "deploy to scrapy cloud project: 592363"
    shub image build 592363 -f ../docker/zyte/Dockerfile -b EDI_ENGINE_BASE_URL=http://tracking.hardcoretech.co:18109/api/ -b EDI_ENGINE_USER=tracking-local -b EDI_ENGINE_TOKEN=LK1YG0FD70TPKCG76RMSCO9HLMK7J23R5ZEJX1VM3607 -b EDI_HOST=tracking.hardcoretech.co
    shub image push 592363
    shub image deploy 592363
else
    echo "invalid -t paramter, one of prd/eval/dev only"
fi
