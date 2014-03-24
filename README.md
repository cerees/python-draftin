
python library to use the draftin.com REST API

Here is a quick example

    from draftin import DraftApi
    api = DraftApi(user, pwd)
    doc = api.create(content, name)
    doc.update(newcontent)
    doc.delete

The object attribute names are as defined in the REST Api docs at https://draftin.com/api

## Todo

Everything except Documents and SavePoints

## License

2 clause BSD License


