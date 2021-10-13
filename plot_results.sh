mkdir -p plots
python plotting_tools/process_tick_log.py
python plotting_tools/process_player_log.py
python plotting_tools/process_sys_log.py $1
if [ "$2" -eq "1" ];
then
  python plotting_tools/process_debug_log.py
fi
if [ "$3" -gt "1" ];
then
  python plotting_tools/plot_multi_iteration.py $4
fi
