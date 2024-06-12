import csv 

class ZHV:
    def __init__(self, path):
        self.path = path
        self.data = []
        self.load_data()
    
    def load_data(self):
        with open(self.path, 'r', encoding="UTF-8") as file:
            rows = file.readlines()
            for row in rows:
                datarow = []
                # Split the row by ; and remove the newline character, and remove the "" from the strings, and convert numbers with , to floats
                for item in row.strip().split('";"'):
                    item = item.replace('"', '')
                    try:
                        if "," in item:
                            datarow.append(float(item.replace(',', '.')))
                        else:
                            datarow.append(item)
                    except:
                        datarow.append(item)
                self.data.append(datarow)
        self.data = self.data[1:]
    
    def get_data(self):
        return self.data

    def get_data_in_bbox(self, minlat, minlon, maxlat, maxlon):
        data_in_bbox = []
        for row in self.data:
            # The data looks like this: SeqNo	Type	DHID	Parent	Name	Latitude	Longitude	MunicipalityCode	Municipality	DistrictCode	District	Description	Authority	DelfiName	THID	TariffProvider	LastOperationDate
            if minlat < float(row[5]) < maxlat and minlon < float(row[6]) < maxlon:
                data_in_bbox.append(row)
        return data_in_bbox

