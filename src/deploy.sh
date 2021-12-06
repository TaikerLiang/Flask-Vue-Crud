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
    shub image build 407697 -f Dockerfile.prd
    shub image push 407697
    shub image deploy 407697
    shub image build 572059 -f Dockerfile.prd
    shub image push 572059
    shub image deploy 572059
elif [ "x$target" = "xeval" ]; then
    echo "deploy to scrapy cloud project: 407696"
    shub image build 407696 -f Dockerfile.eval
    shub image push 407696
    shub image deploy 407696
elif [ "x$target" = "xdev" ]; then
    echo "deploy to scrapy cloud project: 544508"
    shub image build 544508 -f Dockerfile.dev
    shub image push 544508
    shub image deploy 544508
else
    echo "invalid -t paramter, one of prd/eval/dev only"
fi
