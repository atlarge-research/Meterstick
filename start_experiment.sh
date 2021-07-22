source ./config.cfg

# Comment this out if nodes not on DAS5!
./das5_reservation.sh 2 900

# Read list of ips. First node is chosen as MC server.
IPS=(`< ips`)
if [ ${#IPS[@]} -lt 2 ]
    then
        echo "Must provide at least two ips in ips file."
        exit
fi

iteration_start=0

# Handling of SSL keys
mc_key_command=''
ys_key_command=''
username_command=''
if [ "$use_keys" = true ]
then
    mc_key_command="-i ${key_mc}"
    ys_key_command="-i ${key_ys}"
    username_command="${username}@"
fi

# Fault tolerance functionality, retrieves partial results and resumes at cut off point
if [ "$resume" = true ]
    then
        echo "Attempting resuming experiment..."

        if [ "$resume_from_results" = false ]
        then 
            rm -rf results
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
        else
            echo "Using already collected partial results"
        fi
        

        servers_temp=$@
        jmx_urls_temp=$@
        incomplete_worlds=$@
        i=0
        iteration_final=$(($iterations - 1))

        # Check hierarchy: server -> iteration -> worlds
        for server in "${servers[@]}"
        do
            curr_dir="results/${server}"
            if [[ -d "${curr_dir}" ]] 
            then
                # Only find the lowest incomplete iteration
                if [ "$iteration_start" -eq 0 ]; 
                then

                    last_iteration=0
                    found_incomplete=false
                    for ite in $( seq $iteration_start $iteration_final )
                    do
                        last_iteration=$ite
                        curr_iter_dir="${curr_dir}/${ite}"
                        incomplete_worlds=$@
                        
                        # Check if all worlds complete for this iteration
                        for world in "${worlds[@]}"
                        do
                            world_finished=`ls ${curr_iter_dir}/${world} 2>/dev/null | grep -E 'still|tick_log' | wc -l`
                            if [ "$world_finished" -lt "2" ];
                            then
                                incomplete_worlds+=($world)
                            fi
                        done

                        # Check if all worlds in this iteration are complete
                        if [ "${#incomplete_worlds[@]}" -gt "1" ];
                        then
                            # Server iterations not finished                        
                            iteration_start=$ite
                            found_incomplete=true
                        
                            servers_temp+=($server)
                            jmx_urls_temp+=(${jmx_urls[${i}]})
                            break
                        fi
                    done

                    #if [ "$last_iteration" -lt "$iteration_final" ]; 
                    #then
                    #    if [ "$found_incomplete" = false ]
                    #    then
                    #        iteration_start=$last_iteration
                    #        servers_temp+=($server)
                    #        jmx_urls_temp+=(${jmx_urls[${i}]})
                    #    fi
                    #fi

                fi                
                
            else 
                # Server was not run yet
                servers_temp+=($server)
                jmx_urls_temp+=(${jmx_urls[${i}]})
                
            fi
            let "i=i+1"
        done
        servers=("${servers_temp[@]}")  
        jmx_urls=("${jmx_urls_temp[@]}")
        echo -n "Resuming for servers: "
        echo "${servers[*]}"
        echo -n "Resuming at iteration: "
        echo $iteration_start
        echo -n "With worlds: "
        echo "${incomplete_worlds[*]}"

fi


#echo "Copying world:${world} to server folders"
#server_folders=($(ls -d MC/servers/*/))
#for server_folder in "${server_folders[@]}"
#do
#    rm -rf $server_folder/world
#    cp -RT MC/worlds/${world} $server_folder/world > /dev/null
#done


if [ "$already_copied" = false ]
then
    echo "Rsync to MC server node..."
    rsync -rt --del -e "ssh ${mc_key_command}" MC/ ${username_command}${IPS[0]}:$mclocation > /dev/null

    echo "Rsync to yardstick nodes..."
    for ip in ${IPS[@]:1}
    do 
        # Assumes all yardstick nodes have the same file layout. 
        rsync -rt --del -e "ssh ${ys_key_command}" yardstick/ ${username_command}$ip:$yardsticklocation > /dev/null

    done
else    
    echo "Folders already copied to remote, skipping"
fi


# Run MC controllers through ssh
echo -n "Activating MC controller on "
echo ${IPS[0]}
ssh $mc_key_command ${username_command}${IPS[0]} "cd ${mclocation} ; python3 mc_receive.py -c ${controlport} -m ${mcport} -d ${debug_profile} -js ${jmx_port_start} -je ${jmx_port_stop} -ram ${ram} > results/mc_receive_out.txt 2>&1 &"

# About 1 second join time per player, adjust for this
adjusted_duration=$(($duration + $num_players))

# Run yardstick controllers through ssh, with numerical id to differentiate them
i=0
for ip in ${IPS[@]:1}
do 
echo -n "Activating yardstick on "
echo $ip
ssh $ys_key_command ${username_command}${ip} "cd ${yardsticklocation} ; python3 ys_receive.py ${IPS[0]} ${num_players} -b ${bot_behaviour} -box ${bounding_box} -id ${i} -d ${adjusted_duration} -w ${collect_yardstick} -c ${controlport} -m ${mcport} > results/ys_receive_out.txt 2>&1 & "
let "i+=1"
done

if [ "$found_incomplete" = true ]
then
    incomplete_command="-Wi ${incomplete_worlds[*]}"
else
    incomplete_command=''
fi

sleep 3
# Run controller server
python3 controller.py ${IPS[0]} -y ${IPS[@]:1} -s ${servers[@]} -W ${worlds[@]} ${incomplete_command} -ju ${jmx_urls[@]} -w ${collect_yardstick} -c ${controlport} -m ${mcport} -i ${iterations} -is ${iteration_start} -d ${adjusted_duration}

if [ "$resume" = false ] 
then
    rm -rf results
fi

# Collect results
echo -n "Collecting MC results from "
echo ${IPS[0]}
rsync -rt -e "ssh ${mc_key_command}" ${username_command}${IPS[0]}:$mclocation/results/ results/ > /dev/null

for ip in ${IPS[@]:1}
do 
echo -n "Collecting yardstick results from "
echo $ip
rsync -rt -e "ssh ${ys_key_command}" ${username_command}$ip:$yardsticklocation/results/ results/ > /dev/null

done
