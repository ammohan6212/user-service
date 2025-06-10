#!/bin/bash 

git checkout main; 

git fetch --all 

sh path.sh 

git add . ; git commit -m "mohan"; git push origin main ; 

git checkout test; 

git merge main

sh path.sh 

git add . ; git commit -m "mohan"; git push origin test ; 

git checkout dev; 

git merge main

sh path.sh 

git add . ; git commit -m "mohan"; git push origin dev ; 