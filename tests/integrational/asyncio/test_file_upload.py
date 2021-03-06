import pytest

from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.integrational.vcr_helper import pn_vcr
from tests.helper import pnconf_file_copy
from pubnub.endpoints.file_operations.publish_file_message import PublishFileMessage
from pubnub.models.consumer.file import (
    PNSendFileResult, PNGetFilesResult, PNDownloadFileResult,
    PNGetFileDownloadURLResult, PNDeleteFileResult, PNFetchFileUploadS3DataResult, PNPublishFileMessageResult
)


CHANNEL = "files_asyncio_ch"


def send_file(pubnub, file_for_upload, cipher_key=None):
    with open(file_for_upload.strpath, "rb") as fd:
        envelope = yield from pubnub.send_file().\
            channel(CHANNEL).\
            file_name(file_for_upload.basename).\
            message({"test_message": "test"}).\
            should_store(True).\
            ttl(222).\
            cipher_key(cipher_key).\
            file_object(fd).future()

    assert isinstance(envelope.result, PNSendFileResult)
    assert envelope.result.name
    assert envelope.result.timestamp
    assert envelope.result.file_id
    return envelope


@pytest.mark.asyncio
def test_delete_file(event_loop, file_for_upload):
    pubnub = PubNubAsyncio(pnconf_file_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "files_asyncio_uuid"

    envelope = yield from send_file(pubnub, file_for_upload)

    delete_envelope = yield from pubnub.delete_file().\
        channel(CHANNEL).\
        file_id(envelope.result.file_id).\
        file_name(envelope.result.name).future()

    assert isinstance(delete_envelope.result, PNDeleteFileResult)
    pubnub.stop()


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/file_upload/list_files.yaml",
    filter_query_parameters=['uuid', 'seqn', 'pnsdk']
)
@pytest.mark.asyncio
def test_list_files(event_loop):
    pubnub = PubNubAsyncio(pnconf_file_copy(), custom_event_loop=event_loop)
    envelope = yield from pubnub.list_files().channel(CHANNEL).future()

    assert isinstance(envelope.result, PNGetFilesResult)
    assert envelope.result.count == 23
    pubnub.stop()


@pytest.mark.asyncio
def test_send_and_download_file(event_loop, file_for_upload):
    pubnub = PubNubAsyncio(pnconf_file_copy(), custom_event_loop=event_loop)
    envelope = yield from send_file(pubnub, file_for_upload)
    download_envelope = yield from pubnub.download_file().\
        channel(CHANNEL).\
        file_id(envelope.result.file_id).\
        file_name(envelope.result.name).future()

    assert isinstance(download_envelope.result, PNDownloadFileResult)
    pubnub.stop()


@pytest.mark.asyncio
def test_send_and_download_file_encrypted(event_loop, file_for_upload, file_upload_test_data):
    pubnub = PubNubAsyncio(pnconf_file_copy(), custom_event_loop=event_loop)
    envelope = yield from send_file(pubnub, file_for_upload, cipher_key="test")
    download_envelope = yield from pubnub.download_file().\
        channel(CHANNEL).\
        file_id(envelope.result.file_id).\
        file_name(envelope.result.name).\
        cipher_key("test").\
        future()

    assert isinstance(download_envelope.result, PNDownloadFileResult)
    assert download_envelope.result.data == bytes(file_upload_test_data["FILE_CONTENT"], "utf-8")
    pubnub.stop()


@pytest.mark.asyncio
def test_get_file_url(event_loop, file_for_upload):
    pubnub = PubNubAsyncio(pnconf_file_copy(), custom_event_loop=event_loop)
    envelope = yield from send_file(pubnub, file_for_upload)
    file_url_envelope = yield from pubnub.get_file_url().\
        channel(CHANNEL).\
        file_id(envelope.result.file_id).\
        file_name(envelope.result.name).future()

    assert isinstance(file_url_envelope.result, PNGetFileDownloadURLResult)
    pubnub.stop()


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/file_upload/fetch_s3_upload_data.yaml",
    filter_query_parameters=['uuid', 'seqn', 'pnsdk']
)
@pytest.mark.asyncio
def test_fetch_file_upload_s3_data_with_result_invocation(event_loop, file_upload_test_data):
    pubnub = PubNubAsyncio(pnconf_file_copy(), custom_event_loop=event_loop)
    result = yield from pubnub._fetch_file_upload_s3_data().\
        channel(CHANNEL).\
        file_name(file_upload_test_data["UPLOADED_FILENAME"]).result()

    assert isinstance(result, PNFetchFileUploadS3DataResult)
    pubnub.stop()


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/file_upload/publish_file_message_encrypted.yaml",
    filter_query_parameters=['uuid', 'seqn', 'pnsdk']
)
@pytest.mark.asyncio
def test_publish_file_message_with_encryption(event_loop, file_upload_test_data):
    pubnub = PubNubAsyncio(pnconf_file_copy(), custom_event_loop=event_loop)
    envelope = yield from PublishFileMessage(pubnub).\
        channel(CHANNEL).\
        meta({}).\
        message({"test": "test"}).\
        file_id("2222").\
        file_name("test").\
        should_store(True).\
        ttl(222).future()

    assert isinstance(envelope.result, PNPublishFileMessageResult)
    pubnub.stop()
