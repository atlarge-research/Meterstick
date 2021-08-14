# Ensure Java 11 is installed
java --version 2>&1 > /dev/null
result=$?
if [ $result -ne 0 ]
then
	sudo apt-get install -y openjdk-11-jre-headless 2>&1 > /dev/null
fi
