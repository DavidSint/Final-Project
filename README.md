# ReadMe
This was an experiment and a research project. The files included are some of those that helped me collect and analyse the data.

# Environment
The python files were run in a conda environment, of which the environment.yml can be used to download the necessary libraries.

The command for creating the conda environment using the environment.yml is:
```bash
conda env create --name envname -f environment.yml
```

# Data
The data stored in my database is too large for me to share. However, I have pushed them to the repo available on [GitHub](https://github.com/DavidSint/Final-Project). The MongoDB has been dumped to a folder called dump and can be restored to a local MongoDB instance by using the command:
```bash
mongorestore dump
```

