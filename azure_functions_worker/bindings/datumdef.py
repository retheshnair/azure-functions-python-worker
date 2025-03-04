from .. import protos


class Datum:
    def __init__(self, value, type):
        self.value = value
        self.type = type

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        return self.value == other.value and self.type == other.type

    def __hash__(self):
        return hash((type(self), (self.value, self.type)))

    def __repr__(self):
        val_repr = repr(self.value)
        if len(val_repr) > 10:
            val_repr = val_repr[:10] + '...'
        return '<Datum {} {}>'.format(self.type, val_repr)

    @classmethod
    def from_typed_data(cls, td: protos.TypedData):
        tt = td.WhichOneof('data')
        if tt == 'http':
            http = td.http
            val = dict(
                method=Datum(http.method, 'string'),
                url=Datum(http.url, 'string'),
                headers={
                    k: Datum(v, 'string') for k, v in http.headers.items()
                },
                body=(
                    Datum.from_typed_data(http.rawBody)
                    or Datum(type='bytes', value=b'')
                ),
                params={
                    k: Datum(v, 'string') for k, v in http.params.items()
                },
                query={
                    k: Datum(v, 'string') for k, v in http.query.items()
                },
            )
        elif tt == 'string':
            val = td.string
        elif tt == 'bytes':
            val = td.bytes
        elif tt == 'json':
            val = td.json
        elif tt is None:
            return None
        else:
            raise NotImplementedError(
                'unsupported TypeData kind: {!r}'.format(tt)
            )

        return cls(val, tt)


def datum_as_proto(datum: Datum) -> protos.TypedData:
    if datum.type == 'string':
        return protos.TypedData(string=datum.value)
    elif datum.type == 'bytes':
        return protos.TypedData(bytes=datum.value)
    elif datum.type == 'json':
        return protos.TypedData(json=datum.value)
    elif datum.type == 'http':
        return protos.TypedData(http=protos.RpcHttp(
            status_code=datum.value['status_code'].value,
            headers={
                k: v.value
                for k, v in datum.value['headers'].items()
            },
            enable_content_negotiation=False,
            body=datum_as_proto(datum.value['body']),
        ))
    else:
        raise NotImplementedError(
            'unexpected Datum type: {!r}'.format(datum.type)
        )
