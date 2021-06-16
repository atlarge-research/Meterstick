# Download the correct server versions to the server folders given
# Or provide your own servers, given that you place the run.sh file and rename the jar to server.jar
curl https://launcher.mojang.com/v1/objects/35139deedbd5182953cf1caa23835da59ca3d7cd/server.jar -o MC/servers/Vanilla/server.jar
# Forge specific requirement
cp MC/servers/Vanilla/server.jar MC/servers/Forge/minecraft_server.1.16.4.jar
curl https://papermc.io/api/v2/projects/paper/versions/1.16.4/builds/416/downloads/paper-1.16.4-416.jar -o MC/servers/PaperMC/server.jar
