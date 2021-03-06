#!/bin/bash
#Empty check not input parameter and actions
EMPTY=0
if [ $# -eq 0 ]; then
    EMPTY=1
fi
lastParamenter=${!#} 
#inputParameter=$@
#Compare string with list string
containsAction(){
	local e  
	for e in "${@:2}"; do [[ "${e,,}" == "${1,,}" ]] && return 1; done
	return 0
}
descriptionFunction(){
	echo -e "\t./pgtools paramneters Action"
	echo -e "\t* ACTIONS:"
	echo -e "\tlist: List all database in Postgre Server"
	echo -e "\tdbsize: Show size of Database"
	echo -e "\tcreate: Create new database (required DBNAME (-d) in paramneters)"
	echo -e "\tbackup: Backup a database (required DBNAME (-d) in paramneters)"
	echo -e "\trestore: Restore a database (required DBNAME (-d) in paramneters)"
	echo -e "\tdrop: Drop a database (required DBNAME (-d) in paramneters)"
	echo -e "\t* PARAMETERS:"
	echo -e "\t-C= or --container= :Name of container. This parameter is required"
	echo -e "\t-D= or --dbname=    :Name of Database. This parameter is required using with Create, Restore, Drop and Backup database"	
	echo -e "\t-F= or --file=      :Name of file using for Backup, Restore"
}

RestoreDB(){
			if [ -f $FILE ]; then				
				FULLPATH=$(cd $(dirname "$FILE") && pwd -P)/$(basename "$FILE")
				docker exec -it $CONTAINER mkdir -p oetemp
				docker cp $FULLPATH $CONTAINER:/oetemp
				FILENAME=$(basename $FULLPATH)
				echo "Please wait a few minutes"
				docker exec -it $CONTAINER su -c "pg_restore -F t -d $DBNAME /oetemp/$FILENAME" postgres 
				docker exec -it $CONTAINER rm /oetemp -rf
			else
				echo "File not found"
			fi
			}
BackupDB(){				
				echo "Please wait a few minutes"
				docker exec -it $CONTAINER mkdir oetemp
				docker exec -it $CONTAINER su -c "pg_dump -F t -f /oetemp/$FILE $DBNAME" postgres				
				docker cp $CONTAINER:/oetemp/$FILE .
				docker exec -it $CONTAINER rm /oetemp -rf	
			}

LISTACTIONS=("list" "restore" "backup" "dbsize" "create" "drop")
containsAction "$lastParamenter" "${LISTACTIONS[@]}"
if [[ $EMPTY == 1 || "$?" == 0 ]]; then
    descriptionFunction	
	echo "* Please check parameter and Action *"
	exit 1
else
    # whatever you want to do when arr doesn't contain value	
	for i in "$@"
	do
	case $i in
		-C=*|--container=*)
		CONTAINER="${i#*=}"
		shift # past argument=value
		;;
		-F=*|--file=*)
		FILE="${i#*=}"
		shift # past argument=value
		;;
		-D=*|--dbname=*)
		DBNAME="${i#*=}"
		shift # past argument=value
		;;		
		*)
				# unknown option
		;;
	esac
	done
	#Check Container
	if [[ -z $CONTAINER ]]; then
		descriptionFunction
		echo "* Incomplete container parameter *"
		exit 1
	fi
	#List Action
	if [[ "${lastParamenter,,}" == "list" ]]; then
		docker exec -it $CONTAINER su -c "psql --list" postgres
		exit 1
	fi
	
	#DBSize Action
	if [[ "${lastParamenter,,}" == "dbsize" ]]; then
		#Not Input 
		if [[ -z $DBNAME ]]; then
			docker exec -it $CONTAINER su -c 'psql -c "select t1.datname AS db_name, pg_size_pretty(pg_database_size(t1.datname)) as db_size from pg_database t1 order by pg_database_size(t1.datname) desc;"' postgres
			exit 1
		else
			docker exec -it $CONTAINER su -c 'psql -c "select t1.datname AS db_name, pg_size_pretty(pg_database_size(t1.datname)) as db_size from pg_database t1 where t1.datname ilike '\'$DBNAME\'';"' postgres
			exit 1
		fi
	fi
	
	#Check DBNAME	
	if [[ -z $DBNAME ]]; then
		descriptionFunction	
		echo "* Please check DBNAME parameter *"
		exit 1
	fi
	
	#Create Action
	if [[ "${lastParamenter,,}" == "create" ]]; then
		docker exec -it $CONTAINER su -c "psql -c 'CREATE DATABASE \"$DBNAME\" encoding='\'utf8\'';'" postgres
		#Kha la phuc tap Export DBNAME='$DBNAME' (truyen ten databse vao container environment)
		docker exec -it $CONTAINER su -c 'export DBNAME='$DBNAME' && psql -c "ALTER DATABASE \"$DBNAME\" OWNER TO $POSTGRES_USER;"' postgres
		if [[ $FILE ]]; then
			RestoreDB
		fi
		exit 1
	fi
	
	#Restore Action
	if [[ "${lastParamenter,,}" == "restore" ]]; then		
		if [[ $FILE ]]; then
			RestoreDB
		fi
		exit 1
	fi
	
	#Backup Action
	if [[ "${lastParamenter,,}" == "backup" ]]; then		
		BackupDB
		exit 1
	fi
	
	#Drop Action
	if [[ "${lastParamenter,,}" == "drop" ]]; then
		docker exec -it $CONTAINER su -c "dropdb \"$DBNAME\";" postgres
		exit 1
	fi
fi