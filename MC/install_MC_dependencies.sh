# Ensure pip is installed
pip --version 2>&1 > /dev/null
result=$?
if [ $result -ne 0 ]
then
	sudo apt update
	sudo apt install python3-pip
fi

# Ensure mcrcon is installed
pip list | grep mcrcon 2>&1 > /dev/null
result=$?
if [ $result -ne 0 ]
then
	pip install mcrcon 2>&1 > /dev/null
fi

# Ensure psutil is installed
pip list | grep psutil 2>&1 > /dev/null
result=$?
if [ $result -ne 0 ]
then
	pip install psutil 2>&1 > /dev/null
fi

# Ensure Java 11 is installed
java --version 2>&1 > /dev/null
result=$?
if [ $result -ne 0 ]
then
	sudo apt-get install -y openjdk-11-jre-headless 2>&1 > /dev/null
fi
