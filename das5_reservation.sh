# Makes a DAS-5 compute node reservation, gets the nodes, waits for them to be available and writes them to ips file.
if [ $# -eq 0 ]
    then 
        echo "Please provide number of nodes and duration in seconds"
        exit
fi
resnum=$(preserve -np $1 -t $2 | grep "Reservation number" | grep -o [0-9]*)

ready=""
# Continiously check if reservation is ready
while [ -z "$ready" ] 
    do
        echo "Waiting on reservation..."
        sleep 3
        res=$(preserve -llist | grep ${resnum})
        ready=$(echo ${res} | grep -o R)
done

echo $res | grep -o node... > ips

