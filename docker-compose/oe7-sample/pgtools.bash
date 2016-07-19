#!/bin/bash
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
	echo "./pgtools paramneters Action"
	echo "* ACTIONS:"
	echo " 	list: List all database in Postgre Server"
	echo " 	dbsize: Show size of Database"
	echo " 	create: Create new database (required DBNAME (-d) in paramneters)"
	echo " 	backup: Backup a database (required DBNAME (-d) in paramneters)"
	echo " 	restore: Restore a database (required DBNAME (-d) in paramneters)"
	echo " 	drop: Drop a database (required DBNAME (-d) in paramneters)"
	echo "* PARAMETERS:"
	echo " 	-C= or --container= :Name of container. This parameter is required"
	echo " 	-D= or --dbname=    :Name of Database. This parameter is required using with Create, Restore, Drop and Backup database"	
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
		docker exec -it $CONTAINER su -c "psql -c 'CREATE DATABASE \"$DBNAME\" encoding='''utf8''';'" postgres
		#Kha la phuc tap Export DBNAME='$DBNAME' (truyen ten databse vao container environment)
		docker exec -it $CONTAINER su -c 'export DBNAME='$DBNAME' && psql -c "ALTER DATABASE \"$DBNAME\" OWNER TO $POSTGRES_USER;"' postgres
		if [[ $FILE ]]; then
			if [ -f $FILE ]; then				
				FULLPATH=$(cd $(dirname "$FILE") && pwd -P)/$(basename "$FILE")
				docker cp $FULLPATH $CONTAINER:/tmp
				docker exec -it $CONTAINER cat /tmp/$(basename $FULLPATH)
			else
				echo "File not found"
			fi
		fi
		exit 1
	fi
	
	#Drop Action
	if [[ "${lastParamenter,,}" == "drop" ]]; then
		docker exec -it $CONTAINER su -c "dropdb \"$DBNAME\";" postgres
		exit 1
	fi
fi