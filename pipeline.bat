git submodule init
git submodule update

:: if the submodule folder "liliths-throne-public" exists, discard all the changes to it
if exist liliths-throne-public (
	cd liliths-throne-public
	git reset --hard
	git clean -df
	cd ..
)

python ./main.py --no-update-repo %*
