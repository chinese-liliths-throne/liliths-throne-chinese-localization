#!/bin/bash

git submodule init
git submodule update

# if the submodule folder "liliths-throne-public" exists, discard all the changes to it
if [ -d "lilith-mod-pack" ]; then
	cd lilith-mod-pack
	git reset --hard
	git clean -df
	cd ..
fi

python ./main.py --no-update-repo --target mod $*