# From notebook to cloud: Deploy ML model on Ubuntu

## Folder structure

Workshop_root/<br />
├── app/<br />
│   ├── app.py<br />
│   ├── Containerfile<br />
├── model/<br />
│   ├── model.pkl<br />
│   └── vectorizer.pkl<br />
├── dataset/<br />
│   └── dataset.csv<br />
├── notebook/<br />
│   └── mlops.ipynb<br />
├── k8s/<br />
│   ├── deployment.yaml<br />
│   ├── service.yaml<br />
│   └── ingress.yaml<br />
├── README.md<br />
└── requirements.txt<br />
└── <venv_name>


## Steps to follow:

### A. Virtual environment

- Create a virtual environment(venv)
```
python3 -m venv <venv_name>
```
- Activate the venv
```
source <venv_name>/bin/activate
```
- Install the required packages within venv
```
pip install -r requirements.txt
```
- Exit the venv
```
deactivate
```


### B. Dataset

- Follow the link to [download the dataset](https://www.kaggle.com/datasets/mexwell/telegram-spam-or-ham)


### C. Notebook

- Open jupyter notebook
```
jupyter notebook
```
- Change kernel to your virtual environment
- Import the libraraies and then download the nltk files
- Run the cells
- Save the model and vectorizer to model folder for future use.
- Save and checkpoint the notebook


### D. Containerization

- In /app folder, create a file app.py
```python
from fastapi import FastAPI
from pydantic import BaseModel
import joblib

app = FastAPI()

# Load model and vectorizer
model = joblib.load("model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

class TextInput(BaseModel):
    msg: str

@app.post("/predict")
def predict(data: TextInput):
    text = data.msg
    text_vector = vectorizer.transform([text])

    prediction = model.predict(text_vector)
    result = prediction[0]

    return {"sentiment": str(result)}
```

- Create the Containerfile
```
#Lightweight Python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

#Copy dependency list and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#copy the app code
COPY app/app.py .

#Copy the model file
COPY model/model.pkl .
COPY model/vectorizer.pkl .

#Expose the FastAPI port
EXPOSE 8000

#Run the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port","8000"]
```

- Build the image
```
podman build -t <image_name> -f app/Containerfile .
```
- Run the container
```
podman run -d -p 8000:8000 <image_name>
```
- check if all the files are present in the container shell
```
podman run -it <image_name>/bin/bash
/app#
exit
```
- On your browser, visit localhost:8000/docs
- Click on Try it out, edit the msg field and execute.


### E. Setting Microk8s

- Install MicroK8s
```
sudo snap install microk8s --classic --channel=1.30/stable
```
- Add current user to MicroK8s group
```
sudo usermod -a -G microk8s $USER
```
- Apply group change without reboot
```
newgrp microk8s
```
- Check status
```
microk8s status --wait-ready
```
- Enable Kubernetes essentials
```
microk8s enable dns registry ingress
```


### F. Configure Podman to Use an Insecure Local Registry
- Create your personal registries configuration file
```
mkdir -p ~/.config/containers
nano ~/.config/containers/registries.conf
```
- Edit the configuration file to add an insecure registry 
```
[registries.search]
registries = ['docker.io']

[registries.insecure]
registries = ['localhost:32000']

[registries.block]
registries = []
```
- Save the file (Ctrl + O, then Enter)
- Close the file (Ctrl + X).
- Restart the Podman socket
```
systemctl --user restart podman.socket 2>/dev/null || true
```
- Verify your configuration loaded correctly
```
podman info | grep -A3 registries
```
- You should see something like:
```
registries:
  search:
    - docker.io
  insecure_registries:
    - localhost:32000
```


### G. Deployment

- Tag your Podman image for MicroK8s local registry
```
podman tag spam-ham localhost:32000/spam-ham:latest
```
- Push to MicroK8s registry
```
podman push localhost:32000/spam-ham:latest
```
- Apply to Cluster
```
cd k8s
microk8s kubectl apply -f deployment.yaml
microk8s kubectl apply -f service.yaml
microk8s kubectl apply -f ingress.yaml
echo "127.0.0.1 spam.ham" | sudo tee -a /etc/hosts
```


### H. Testing the endpoint

- Test a case where the output is spam
```
curl http://spam.ham/predict \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"msg": "Unbelievable offer! Buy 1 get 4 free, click on this link to claim"}'
```
- Test a case where the output is ham
```
curl http://spam.ham/predict \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"msg": "I am attending Ubucon India 2025!"}'
```




