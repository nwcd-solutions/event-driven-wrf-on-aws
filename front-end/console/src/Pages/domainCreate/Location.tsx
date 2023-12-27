import React, { useState,useEffect } from "react";
import {
  Button,
  Flex,
  VisuallyHidden,
  View
} from "@aws-amplify/ui-react";
import * as XLSX from 'xlsx';
import Spreadsheet from "react-spreadsheet";

interface LocationProps { 
  location: [];
  onUpdate:(location:any)=>void;
}

const Location = ( {location:location_data,onUpdate}:LocationProps) => {
  const [locationdata, setLocationdata] = useState<any>(
    [
      [
        { value: "" },
      ],
    ]
  );


  const loadLocationFile = () => {
    const fileInput = document.getElementById('location');
    if (fileInput !== undefined && fileInput !== null)
      fileInput.click();  
  }
  
  useEffect(() => { 
    let data = [
      [
        { value: "" },
      ],
    ];
    if (location_data.length>0 ){
      data = location_data.map((row:any) =>
        row.map((value:any) => ({ value }))
      );
    };   

    setLocationdata(data);

  },[location_data]);

  const onFilePickerChange = (file:any) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const { result } = event.target as FileReader;
        const workbook = XLSX.read(result, { type: 'binary' });
        const sheetName = workbook.SheetNames[0];
        const sheet = workbook.Sheets[sheetName];
        const data = XLSX.utils.sheet_to_json(sheet, { header: 1 });
        onUpdate(data);
     
      } catch (e) {
        console.error(e);
      }
    };
    reader.readAsBinaryString(file);

  };

  const handleChange =(d:any) =>{
    //console.log(d);
    const regex = /^[0-9.]+$/;
    const result = d.map((innerArray:any) =>
    innerArray.map((obj:any) => {
      const value = obj.value;
      return regex.test(value) ? parseFloat(value) : value;
    })
  );
    //const result = d.map((arr:any) => arr.map((obj:any) => obj.value));
    console.log("result:",result);
    onUpdate(result);
  }

  return (
    <>
    <View>
        <br></br>
        <div style={{ maxHeight: "350px", overflowY: "auto" }}>
        <Spreadsheet
          data={locationdata}
          onChange={handleChange}
        />     
        </div>   
        <br></br>
        <Flex>
        <Button onClick={() => loadLocationFile() }>Uplaod New Location File</Button>
        </Flex>
        <VisuallyHidden>
          <input type="file" id='location' accept='.csv,.xlsx' onChange={e => onFilePickerChange(e.target.files?.[0]) } />
        </VisuallyHidden>
    </View>        
    </>
  );
};

export default Location;
