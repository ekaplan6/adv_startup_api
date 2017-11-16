How to Run:

```
pip install -r requirements.txt
python main.py
```

How to Deploy:
```
gcloud app deploy
```


How to run a custom Docker image:
```
gcloud beta app gen-config --custom
```
Doing the above will add a working Dockerfile to your
project, add a .dockerignore, and modify your `app.yaml`
to use the Dockerfile instead of a pre-selected
base image
