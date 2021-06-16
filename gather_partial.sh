source ./config.cfg

# Use to retrieve results for diagnosis in event of crash
IPS=(`< ips`)
if [ ${#IPS[@]} -lt 2 ]
    then
        echo "Must provide at least two ips in ips file."
        exit
fi


mc_key_command=''
ys_key_command=''
username_command=''
if [ "$use_keys" = true ]
then
    mc_key_command="-i ${key_mc}"
    ys_key_command="-i ${key_ys}"
    username_command="${username}@"
fi


# Collect results
echo -n "Collecting partial MC results from "
echo ${IPS[0]}
rsync -rt -e "ssh ${mc_key_command}" ${username_command}${IPS[0]}:$mclocation/results/ results/ > /dev/null

for ip in ${IPS[@]:1}
do 
echo -n "Collecting partial yardstick results from "
echo $ip
rsync -rt -e "ssh ${ys_key_command}" ${username_command}$ip:$yardsticklocation/results/ results/ > /dev/null

done