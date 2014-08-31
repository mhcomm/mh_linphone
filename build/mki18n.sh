#!/bin/sh
cd `dirname $0`
curdir=`pwd`

echo creating pot file
pygettext --no-location -p ../pylib/lpresources/locale/src -o mh_linphone.pot .

# to create a new language use msginit -l bla bla bla

cd ../pylib/lpresources/locale/src

for lang in fr en ; do
    mkdir -p ../$lang/LC_MESSAGES
    echo "merging <$lang>"
    msgmerge -s -U mh_linphone.$lang.po mh_linphone.pot
done

$curdir/mki18n_mo.sh
