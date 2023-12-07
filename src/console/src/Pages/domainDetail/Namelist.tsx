import React, { useState,useEffect } from "react";
import {
  Button,
  Flex,
  TextAreaField,
  VisuallyHidden,
  View
} from "@aws-amplify/ui-react";

interface NamelistProps { 
  namelist: string;
  type:string;
  onUpdate:(namelist:string,type:string)=>void;
}

const Namelist = ( {namelist:nl,type:filetype,onUpdate}:NamelistProps) => {
  const [namelist, setNamelist] = useState<string>('');
  const [acceptFileTypes ,setAcceptFileTypes]= useState('');

  const loadNamelistFile = (type:string) => {
    const fileInput = document.getElementById(type);
    if (fileInput !== undefined && fileInput !== null)
      fileInput.click();  
  }
  
  useEffect(() => { 
     setNamelist(nl);
     if (filetype == 'wrf_bk')
       setAcceptFileTypes('.input');
     else if (filetype == 'wps')
       setAcceptFileTypes('.wps');
     else if (filetype == 'wrf')
       setAcceptFileTypes('.input');

  },[nl]);

  const onFilePickerChange = (file:any) => {
    const reader = new FileReader();
    reader.onload = () => {
      onUpdate(reader.result as string,filetype);
    };
    reader.readAsText(file);
  };

  const handleUpdate =() =>{
      onUpdate(namelist,filetype);
  }

  return (
    <>
    <View>
        <br></br>
        <TextAreaField 
            label="" 
            defaultValue={namelist} 
            rows={15}
            spellCheck = {false}
            onChange={(e) => setNamelist(e.target.value)}
            onBlur={ handleUpdate}
        >                               
        </TextAreaField>
        <br></br>
        <Flex>
        <Button onClick={() => loadNamelistFile(filetype) }>Uplaod New Config File</Button>
        </Flex>
        <VisuallyHidden>
          <input type="file" id={filetype} accept={acceptFileTypes} onChange={e => onFilePickerChange(e.target.files?.[0]) } />
        </VisuallyHidden>
    </View>        
    </>
  );
};

export default Namelist;
