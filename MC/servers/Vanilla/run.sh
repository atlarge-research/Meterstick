# Runs server in background and reports it's pid.
# First arg is file to pipe server output to.
# Second arg is amount of RAM

java -Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.port=$3 -Dcom.sun.management.jmxremote.ssl=false $2 -jar server.jar nogui > $1 2>&1 & echo $!
