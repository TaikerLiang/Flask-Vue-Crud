# -t: options, prd/eval/dev
# ex: sh deploy -t prd

while getopts t: flag
do
    case "${flag}" in
        t) target=${OPTARG};;
    esac
done

if [ "x$target" = "xprd" ]; then
    echo "deploy to scrapy cloud project: 407697"
    shub image build 407697 -f Dockerfile.prd
    shub image push 407697
    shub image deploy 407697
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
