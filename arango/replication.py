from __future__ import absolute_import, unicode_literals

__all__ = ['Replication']

from arango.api import APIWrapper
from arango.exceptions import (
    ReplicationApplierConfigError,
    ReplicationApplierConfigSetError,
    ReplicationApplierStartError,
    ReplicationApplierStateError,
    ReplicationApplierStopError,
    ReplicationClusterInventoryError,
    ReplicationDumpBatchCreateError,
    ReplicationDumpBatchDeleteError,
    ReplicationDumpBatchExtendError,
    ReplicationDumpError,
    ReplicationInventoryError,
    ReplicationLoggerFirstTickError,
    ReplicationLoggerStateError,
    ReplicationMakeSlaveError,
    ReplicationServerIDError,
    ReplicationSyncError
)
from arango.formatter import (
    format_replication_applier_config,
    format_replication_applier_state,
    format_replication_header,
    format_replication_inventory,
    format_replication_logger_state,
    format_replication_sync
)
from arango.request import Request


class Replication(APIWrapper):

    def __init__(self, connection, executor):
        super(Replication, self).__init__(connection, executor)

    def inventory(self, batch_id, include_system=None, all_databases=None):
        """Return an overview of collections and indexes.

        :param batch_id: Batch ID. For RocksDB engine only.
        :type batch_id: str | unicode
        :param include_system: Include system collections in the result.
            Default value is True.
        :type include_system: bool
        :param all_databases: Include all databases. Only works on "_system"
            database. Default value is False.
        :type all_databases: bool
        :return: Overview of collections and indexes.
        :rtype: dict
        :raise arango.exceptions.ReplicationInventoryError: If retrieval fails.
        """
        params = {'batchId': batch_id}
        if include_system is not None:
            params['includeSystem'] = include_system
        if all_databases is not None:
            params['global'] = all_databases

        request = Request(
            method='get',
            endpoint='/_api/replication/inventory',
            params=params
        )

        def response_handler(resp):
            if resp.is_success:
                return format_replication_inventory(resp.body)
            raise ReplicationInventoryError(resp, request)

        return self._execute(request, response_handler)

    def create_dump_batch(self, ttl=None):
        """Create a new dump batch.

        :param ttl: Time-to-live for the new batch in seconds.
        :type ttl: int
        :return: ID of the batch.
        :rtype: dict
        :raise arango.exceptions.ReplicationDumpBatchCreateError: If create
            fails.
        """
        request = Request(
            method='post',
            endpoint='/_api/replication/batch',
            data={'ttl': ttl}
        )

        def response_handler(resp):
            if resp.is_success:
                return {
                    'id': resp.body['id'],
                    'last_tick': resp.body['lastTick']
                }
            raise ReplicationDumpBatchCreateError(resp, request)

        return self._execute(request, response_handler)

    def delete_dump_batch(self, batch_id):
        """Delete a dump batch.

        :param batch_id: Dump batch ID.
        :type batch_id: str | unicode
        :return: True if deletion was successful.
        :rtype: bool
        :raise arango.exceptions.ReplicationDumpBatchDeleteError: If delete
            fails.
        """
        request = Request(
            method='delete',
            endpoint='/_api/replication/batch/{}'.format(batch_id),
            deserialize=False
        )

        def response_handler(resp):
            if resp.is_success:
                return True
            raise ReplicationDumpBatchDeleteError(resp, request)

        return self._execute(request, response_handler)

    def extend_dump_batch(self, batch_id, ttl):
        """Extend a dump batch.

        :param batch_id: Dump batch ID.
        :type batch_id: str | unicode
        :param ttl: Time-to-live for the new batch in seconds.
        :type ttl: int
        :return: True if operation was successful.
        :rtype: bool
        :raise arango.exceptions.ReplicationDumpBatchExtendError: If operation
            fails.
        """
        request = Request(
            method='put',
            endpoint='/_api/replication/batch/{}'.format(batch_id),
            data={'ttl': ttl},
            deserialize=False
        )

        def response_handler(resp):
            if resp.is_success:
                return True
            raise ReplicationDumpBatchExtendError(resp, request)

        return self._execute(request, response_handler)

    def dump(self,
             collection,
             batch_id=None,
             lower=None,
             upper=None,
             chunk_size=None,
             include_system=None,
             ticks=None,
             flush=None,
             deserialize=False):
        """Return the events data of one collection.

        :param collection: Name or ID of the collection to dump.
        :type collection: str | unicode
        :param chunk_size: Size of the result in bytes. This value is honored
            approximately only.
        :type chunk_size: int
        :param batch_id: Batch ID. For RocksDB engine only.
        :type batch_id: str | unicode
        :param lower: Lower bound tick value for results. For MMFiles only.
        :type lower: str | unicode
        :param upper: Upper bound tick value for results. For MMFiles only.
        :type upper: str | unicode
        :param include_system: Include system collections in the result. For
            MMFiles only. Default value is True.
        :type include_system: bool
        :param ticks: Whether to include tick values in the dump. For MMFiles
            only. Default value is True.
        :type ticks: bool
        :param flush: Whether to flush the WAL before dumping. Default value is
            True.
        :type flush: bool
        :param deserialize: Deserialize the response content. Default is False.
        :type deserialize: bool
        :return: Collection events data.
        :rtype: str | unicode | [dict]
        :raise arango.exceptions.ReplicationDumpError: If retrieval fails.
        """
        params = {'collection': collection}

        if chunk_size is not None:
            params['chunkSize'] = chunk_size
        if batch_id is not None:
            params['batchId'] = batch_id
        if lower is not None:
            params['from'] = lower
        if upper is not None:
            params['to'] = upper
        if include_system is not None:
            params['includeSystem'] = include_system
        if ticks is not None:
            params['ticks'] = ticks
        if flush is not None:
            params['flush '] = flush

        request = Request(
            method='get',
            endpoint='/_api/replication/dump',
            params=params,
            deserialize=False
        )

        def response_handler(resp):
            if resp.is_success:
                result = format_replication_header(resp.headers)
                print(resp.body)
                result['content'] = [
                    self._conn.deserialize(line) for
                    line in resp.body.split('\n') if line
                ] if deserialize else resp.body
                return result

            raise ReplicationDumpError(resp, request)

        return self._execute(request, response_handler)

    def synchronize(self,
                    endpoint,
                    database=None,
                    username=None,
                    password=None,
                    include_system=None,
                    incremental=None,
                    restrict_type=None,
                    restrict_collections=None,
                    initial_sync_wait_time=None):  # pragma: no cover
        """Synchronize data from a remote endpoint.

        :param endpoint: Master endpoint (e.g. "tcp://192.168.173.13:8529").
        :type endpoint: str | unicode
        :param database: Database name.
        :type database: str | unicode
        :param username: Username.
        :type username: str | unicode
        :param password: Password.
        :type password: str | unicode
        :param include_system: Whether to include system collection operations.
        :type include_system: bool
        :param incremental: If set to True, then an incremental synchronization
            method is used for synchronizing data in collections. This
            method is useful when collections already exist locally, and only
            the remaining differences need to be transferred from the remote
            endpoint. In this case, the incremental synchronization can be
            faster than a full synchronization. Default value is False, meaning
            complete data is transferred.
        :type incremental: bool
        :param restrict_type: Optional string value for collection filtering.
            Allowed values are "include" or "exclude".
        :type restrict_type: str | unicode
        :param restrict_collections: Optional list of collections for use with
            argument **restrict_type**. If **restrict_type** set to "include",
            only the specified collections are synchronised. Otherwise, all but
            the specified ones are synchronized.
        :type restrict_collections: [str | unicode]
        :param initial_sync_wait_time: Maximum wait time in seconds that the
            initial synchronization will wait for a response from master when
            fetching collection data. This can be used to control after what
            time the initial synchronization will give up waiting for response
            and fail. Value is ignored if set to 0.
        :type initial_sync_wait_time: int
        :return: Collections transferred and last log tick.
        :rtype: dict
        :raise arango.exceptions.ReplicationSyncError: If sync fails.
        """
        data = {'endpoint': endpoint}

        if database is not None:
            data['database'] = database
        if username is not None:
            data['username'] = username
        if password is not None:
            data['password'] = password
        if include_system is not None:
            data['includeSystem'] = include_system
        if incremental is not None:
            data['incremental'] = incremental
        if restrict_type is not None:
            data['restrictType'] = restrict_type
        if restrict_collections is not None:
            data['restrictCollections'] = restrict_collections
        if initial_sync_wait_time is not None:
            data['initialSyncMaxWaitTime'] = initial_sync_wait_time

        request = Request(
            method='put',
            endpoint='/_api/replication/sync',
            data=data
        )

        def response_handler(resp):
            if resp.is_success:
                return format_replication_sync(resp.body)
            raise ReplicationSyncError(resp, request)

        return self._execute(request, response_handler)

    def cluster_inventory(self, include_system=None):
        """Return an overview of collections and indexes in a cluster.

        :param include_system: Include system collections in the result.
            Default value is True.
        :type include_system: bool
        :return: Overview of collections and indexes on the cluster.
        :rtype: dict
        :raise arango.exceptions.ReplicationClusterInventoryError: If retrieval
            fails.
        """
        params = {}
        if include_system is not None:
            params['includeSystem'] = include_system

        request = Request(
            method='get',
            endpoint='/_api/replication/clusterInventory',
            params=params
        )

        def response_handler(resp):
            if resp.is_success:  # pragma: no cover
                return format_replication_inventory(resp.body)
            raise ReplicationClusterInventoryError(resp, request)

        return self._execute(request, response_handler)

    def logger_state(self):
        """Return the state of the replication logger.

        :return: Logger state.
        :rtype: dict
        :raise arango.exceptions.ReplicationLoggerStateError: If retrieval
            fails.
        """
        request = Request(
            method='get',
            endpoint='/_api/replication/logger-state',
        )

        def response_handler(resp):
            if resp.is_success:
                return format_replication_logger_state(resp.body)
            raise ReplicationLoggerStateError(resp, request)

        return self._execute(request, response_handler)

    def logger_first_tick(self):
        """Return the first available tick value from the server.

        :return: First tick value.
        :rtype: str | unicode
        :raise arango.exceptions.ReplicationLoggerFirstTickError: If retrieval
            fails.
        """
        request = Request(
            method='get',
            endpoint='/_api/replication/logger-first-tick',
        )

        def response_handler(resp):
            if resp.is_success:
                return resp.body['firstTick']
            raise ReplicationLoggerFirstTickError(resp, request)

        return self._execute(request, response_handler)

    def applier_config(self):
        """Return the configuration of the replication applier.

        :return: Configuration of the replication applier.
        :rtype: dict
        :raise arango.exceptions.ReplicationApplierConfigError: If retrieval
            fails.
        """
        request = Request(
            method='get',
            endpoint='/_api/replication/applier-config',
        )

        def response_handler(resp):
            if resp.is_success:
                return format_replication_applier_config(resp.body)
            raise ReplicationApplierConfigError(resp, request)

        return self._execute(request, response_handler)

    def set_applier_config(self,
                           endpoint,
                           database=None,
                           username=None,
                           password=None,
                           max_connect_retries=None,
                           connect_timeout=None,
                           request_timeout=None,
                           chunk_size=None,
                           auto_start=None,
                           adaptive_polling=None,
                           include_system=None,
                           auto_resync=None,
                           auto_resync_retries=None,
                           initial_sync_max_wait_time=None,
                           connection_retry_wait_time=None,
                           idle_min_wait_time=None,
                           idle_max_wait_time=None,
                           require_from_present=None,
                           verbose=None,
                           restrict_type=None,
                           restrict_collections=None):
        """Set configuration values of the replication applier.

        :param endpoint: Server endpoint (e.g. "tcp://192.168.173.13:8529").
        :type endpoint: str | unicode
        :param database: Database name.
        :type database: str | unicode
        :param username: Username.
        :type username: str | unicode
        :param password: Password.
        :type password: str | unicode
        :param max_connect_retries: Maximum number of connection attempts the
            applier makes in a row before stopping itself.
        :type max_connect_retries: int
        :param connect_timeout: Timeout in seconds when attempting to connect
            to the endpoint. This value is used for each connection attempt.
        :type connect_timeout: int
        :param request_timeout: Timeout in seconds for individual requests to
            the endpoint.
        :type request_timeout: int
        :param chunk_size: Requested maximum size in bytes for log transfer
            packets when the endpoint is contacted.
        :type chunk_size: int
        :param auto_start: Whether to auto-start the replication applier on
            (next and following) server starts.
        :type auto_start: bool
        :param adaptive_polling: If set to True, replication applier sleeps
            for an increasingly long period in case the logger server at the
            endpoint has no replication events to apply. Using adaptive polling
            reduces the amount of work done by both the applier and the logger
            server when there are infrequent changes. The downside is that it
            might take longer for the replication applier to detect new events.
        :type adaptive_polling: bool
        :param include_system: Whether system collection operations are
            applied.
        :type include_system: bool
        :param auto_resync: Whether the slave should perform a full automatic
            resynchronization with the master in case the master cannot serve
            log data requested by the slave, or when the replication is started
            and no tick value can be found.
        :type auto_resync: bool
        :param auto_resync_retries: Max number of resynchronization retries.
            Setting this to 0 disables it.
        :type auto_resync_retries: int
        :param initial_sync_max_wait_time: Max wait time in seconds the initial
            synchronization waits for master on collection data. This value
            is relevant even for continuous replication when **auto_resync** is
            set to True because this may re-start the initial synchronization
            when master cannot provide log data slave requires. This value is
            ignored if set to 0.
        :type initial_sync_max_wait_time: int
        :param connection_retry_wait_time: Time in seconds the applier idles
            before trying to connect to master in case of connection problems.
            This value is ignored if set to 0.
        :type connection_retry_wait_time: int
        :param idle_min_wait_time: Minimum wait time in seconds the applier
            idles before fetching more log data from the master in case the
            master has already sent all its log data. This wait time can be
            used to control the frequency with which the replication applier
            sends HTTP log fetch requests to the master in case there is no
            write activity on the master. This value is ignored if set to 0.
        :type idle_min_wait_time: int
        :param idle_max_wait_time: Maximum wait time in seconds the applier
            idles before fetching more log data from the master in case the
            master has already sent all its log data. This wait time can be
            used to control the maximum frequency with which the replication
            applier sends HTTP log fetch requests to the master in case there
            is no write activity on the master. Applies only when argument
            **adaptive_polling** is set to True. This value is ignored if set
            to 0.
        :type idle_max_wait_time: int
        :param require_from_present: If set to True, replication applier checks
            at start whether the start tick from which it starts or resumes
            replication is still present on the master. If not, then there
            would be data loss. If set to True, the replication applier aborts
            with an appropriate error message. If set to False, the applier
            still starts and ignores the data loss.
        :type require_from_present: bool
        :param verbose: If set to True, a log line is emitted for all
            operations performed by the replication applier. This should be
            used for debugging replication problems only.
        :type verbose: bool
        :param restrict_type: Optional string value for collection filtering.
            Allowed values are "include" or "exclude".
        :type restrict_type: str | unicode
        :param restrict_collections: Optional list of collections for use with
            argument **restrict_type**. If **restrict_type** set to "include",
            only the specified collections are included. Otherwise, only the
            specified collections are excluded.
        :type restrict_collections: [str | unicode]
        :return: Updated configuration.
        :rtype: dict
        :raise arango.exceptions.ReplicationApplierConfigSetError: If update
            fails.
        """
        data = {'endpoint': endpoint}

        if database is not None:
            data['database'] = database
        if username is not None:
            data['username'] = username
        if password is not None:
            data['password'] = password
        if max_connect_retries is not None:
            data['maxConnectRetries'] = max_connect_retries
        if connect_timeout is not None:
            data['connectTimeout'] = connect_timeout
        if request_timeout is not None:
            data['requestTimeout'] = request_timeout
        if chunk_size is not None:
            data['chunkSize'] = chunk_size
        if auto_start is not None:
            data['autoStart'] = auto_start
        if adaptive_polling is not None:
            data['adaptivePolling'] = adaptive_polling
        if include_system is not None:
            data['includeSystem'] = include_system
        if auto_resync is not None:
            data['autoResync'] = auto_resync
        if auto_resync_retries is not None:
            data['autoResyncRetries'] = auto_resync_retries
        if initial_sync_max_wait_time is not None:
            data['initialSyncMaxWaitTime'] = initial_sync_max_wait_time
        if connection_retry_wait_time is not None:
            data['connectionRetryWaitTime'] = connection_retry_wait_time
        if idle_min_wait_time is not None:
            data['idleMinWaitTime'] = idle_min_wait_time
        if idle_max_wait_time is not None:
            data['idleMaxWaitTime'] = idle_max_wait_time
        if require_from_present is not None:
            data['requireFromPresent'] = require_from_present
        if verbose is not None:
            data['verbose'] = verbose
        if restrict_type is not None:
            data['restrictType'] = restrict_type
        if restrict_collections is not None:
            data['restrictCollections'] = restrict_collections

        request = Request(
            method='put',
            endpoint='/_api/replication/applier-config',
            data=data
        )

        def response_handler(resp):
            if resp.is_success:
                return format_replication_applier_config(resp.body)
            raise ReplicationApplierConfigSetError(resp, request)

        return self._execute(request, response_handler)

    def applier_state(self):
        """Return the state of the replication applier

        :return: Applier state and details.
        :rtype: dict
        :raise arango.exceptions.ReplicationApplierStateError: If retrieval
            fails.
        """
        request = Request(
            method='get',
            endpoint='/_api/replication/applier-state',
        )

        def response_handler(resp):
            if resp.is_success:
                return format_replication_applier_state(resp.body)
            raise ReplicationApplierStateError(resp, request)

        return self._execute(request, response_handler)

    def start_applier(self, last_tick=None):
        """Start the replication applier.

        :param last_tick: The remote last log tick value from which to start
            applying replication. If not specified, the last saved tick from
            the previous applier run is used. If there is no previous applier
            state saved, the applier starts at the beginning of the logger
            server's log.
        :type last_tick: str | unicode
        :return: Applier state and details.
        :rtype: dict
        :raise arango.exceptions.ReplicationApplierStartError: If operation
            fails.
        """
        request = Request(
            method='put',
            endpoint='/_api/replication/applier-start',
            params={'from': last_tick}
        )

        def response_handler(resp):
            if resp.is_success:
                return format_replication_applier_state(resp.body)
            raise ReplicationApplierStartError(resp, request)

        return self._execute(request, response_handler)

    def stop_applier(self):
        """Stop the replication applier.

        :return: Applier state and details.
        :rtype: dict
        :raise arango.exceptions.ReplicationApplierStopError: If operation
            fails.
        """
        request = Request(
            method='put',
            endpoint='/_api/replication/applier-stop',
        )

        def response_handler(resp):
            if resp.is_success:
                return format_replication_applier_state(resp.body)
            raise ReplicationApplierStopError(resp, request)

        return self._execute(request, response_handler)

    def make_slave(self,
                   endpoint,
                   database=None,
                   username=None,
                   password=None,
                   restrict_type=None,
                   restrict_collections=None,
                   include_system=None,
                   max_connect_retries=None,
                   connect_timeout=None,
                   request_timeout=None,
                   chunk_size=None,
                   adaptive_polling=None,
                   auto_resync=None,
                   auto_resync_retries=None,
                   initial_sync_max_wait_time=None,
                   connection_retry_wait_time=None,
                   idle_min_wait_time=None,
                   idle_max_wait_time=None,
                   require_from_present=None,
                   verbose=None):  # pragma: no cover
        """Change the server role to slave.

        :param endpoint: Master endpoint (e.g. "tcp://192.168.173.13:8529").
        :type endpoint: str | unicode
        :param database: Database name.
        :type database: str | unicode
        :param username: Username.
        :type username: str | unicode
        :param password: Password.
        :type password: str | unicode
        :param include_system: Whether system collection operations are
            applied.
        :type include_system: bool
        :param restrict_type: Optional string value for collection filtering.
            Allowed values are "include" or "exclude".
        :type restrict_type: str | unicode
        :param restrict_collections: Optional list of collections for use with
            argument **restrict_type**. If **restrict_type** set to "include",
            only the specified collections are included. Otherwise, only the
            specified collections are excluded.
        :type restrict_collections: [str | unicode]
        :param max_connect_retries: Maximum number of connection attempts the
            applier makes in a row before stopping itself.
        :type max_connect_retries: int
        :param connect_timeout: Timeout in seconds when attempting to connect
            to the endpoint. This value is used for each connection attempt.
        :type connect_timeout: int
        :param request_timeout: Timeout in seconds for individual requests to
            the endpoint.
        :type request_timeout: int
        :param chunk_size: Requested maximum size in bytes for log transfer
            packets when the endpoint is contacted.
        :type chunk_size: int
        :param adaptive_polling: If set to True, replication applier sleeps
            for an increasingly long period in case the logger server at the
            endpoint has no replication events to apply. Using adaptive polling
            reduces the amount of work done by both the applier and the logger
            server when there are infrequent changes. The downside is that it
            might take longer for the replication applier to detect new events.
        :type adaptive_polling: bool
        :param auto_resync: Whether the slave should perform a full automatic
            resynchronization with the master in case the master cannot serve
            log data requested by the slave, or when the replication is started
            and no tick value can be found.
        :type auto_resync: bool
        :param auto_resync_retries: Max number of resynchronization retries.
            Setting this to 0 disables it.
        :type auto_resync_retries: int
        :param initial_sync_max_wait_time: Max wait time in seconds the initial
            synchronization waits for master on collection data. This value
            is relevant even for continuous replication when **auto_resync** is
            set to True because this may restart the initial synchronization
            when master cannot provide log data slave requires. This value is
            ignored if set to 0.
        :type initial_sync_max_wait_time: int
        :param connection_retry_wait_time: Time in seconds the applier idles
            before trying to connect to master in case of connection problems.
            This value is ignored if set to 0.
        :type connection_retry_wait_time: int
        :param idle_min_wait_time: Minimum wait time in seconds the applier
            idles before fetching more log data from the master in case the
            master has already sent all its log data. This wait time can be
            used to control the frequency with which the replication applier
            sends HTTP log fetch requests to the master in case there is no
            write activity on the master. This value is ignored if set to 0.
        :type idle_min_wait_time: int
        :param idle_max_wait_time: Maximum wait time in seconds the applier
            idles before fetching more log data from the master in case the
            master has already sent all its log data. This wait time can be
            used to control the maximum frequency with which the replication
            applier sends HTTP log fetch requests to the master in case there
            is no write activity on the master. Applies only when argument
            **adaptive_polling** is set to True. This value is ignored if set
            to 0.
        :type idle_max_wait_time: int
        :param require_from_present: If set to True, replication applier checks
            at start whether the start tick from which it starts or resumes
            replication is still present on the master. If not, then there
            would be data loss. If set to True, the replication applier aborts
            with an appropriate error message. If set to False, the applier
            still starts and ignores the data loss.
        :type require_from_present: bool
        :param verbose: If set to True, a log line is emitted for all
            operations performed by the replication applier. This should be
            used for debugging replication problems only.
        :type verbose: bool
        :return: Replication details.
        :rtype: dict
        :raise arango.exceptions.ReplicationApplierStopError: If operation
            fails.
        """
        data = {'endpoint': endpoint}

        if database is not None:
            data['database'] = database
        if username is not None:
            data['username'] = username
        if password is not None:
            data['password'] = password
        if restrict_type is not None:
            data['restrictType'] = restrict_type
        if restrict_collections is not None:
            data['restrictCollections'] = restrict_collections
        if include_system is not None:
            data['includeSystem'] = include_system
        if max_connect_retries is not None:
            data['maxConnectRetries'] = max_connect_retries
        if connect_timeout is not None:
            data['connectTimeout'] = connect_timeout
        if request_timeout is not None:
            data['requestTimeout'] = request_timeout
        if chunk_size is not None:
            data['chunkSize'] = chunk_size
        if adaptive_polling is not None:
            data['adaptivePolling'] = adaptive_polling
        if auto_resync is not None:
            data['autoResync'] = auto_resync
        if auto_resync_retries is not None:
            data['autoResyncRetries'] = auto_resync_retries
        if initial_sync_max_wait_time is not None:
            data['initialSyncMaxWaitTime'] = initial_sync_max_wait_time
        if connection_retry_wait_time is not None:
            data['connectionRetryWaitTime'] = connection_retry_wait_time
        if idle_min_wait_time is not None:
            data['idleMinWaitTime'] = idle_min_wait_time
        if idle_max_wait_time is not None:
            data['idleMaxWaitTime'] = idle_max_wait_time
        if require_from_present is not None:
            data['requireFromPresent'] = require_from_present
        if verbose is not None:
            data['verbose'] = verbose

        request = Request(
            method='put',
            endpoint='/_api/replication/make-slave',
            data=data
        )

        def response_handler(resp):
            if resp.is_success:
                return format_replication_applier_state(resp.body)
            raise ReplicationMakeSlaveError(resp, request)

        return self._execute(request, response_handler)

    def server_id(self):
        """Return this server's ID.

        :return: Server ID.
        :rtype: str | unicode
        :raise arango.exceptions.ReplicationServerIDError: If retrieval fails.
        """
        request = Request(
            method='get',
            endpoint='/_api/replication/server-id',
        )

        def response_handler(resp):
            if resp.is_success:
                return resp.body['serverId']
            raise ReplicationServerIDError(resp, request)

        return self._execute(request, response_handler)
