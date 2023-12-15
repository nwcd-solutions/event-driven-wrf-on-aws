import React ,{ useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { View, Heading, ScrollView ,Divider,SwitchField,Text,Flex,Button,Loader } from "@aws-amplify/ui-react";
import ParaTable from "./ParameterList";
import { Parameter } from "./Parameter"
import  EditParameter from "./ParameterEdit";
import { get,put } from 'aws-amplify/api';
import { Modal } from 'react-bootstrap';
interface SettingsProps {
  getToken:()=>void;
}

const Tasks = ({getToken}:SettingsProps) => {

  const navigate = useNavigate();
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [parameter , setParameter] =useState<Parameter>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);
  const [mode_type,setMode_type] = useState(false);
  const [showUpdateModal, setShowUpdateModal] = useState(false)

  async function updateParameter(name:string,value:string){
    console.log('parameter: ', name,value);
    try{
      put({
        apiName: 'WrfAPIGateway',
        path: '/parameter/',              
        options: {
          headers: {
            Authorization: await getToken()!,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
          },
          body: {
            "name":name,
            "value":value
          },
        }
      });
      
    }catch (err) {
      console.log('PUT call failed: ', err);
    }
  }

  async function loadParameters() {
    setLoading(true);
    try {
     
      console.log('get token: ', await getToken());
      const { body } = await get({
        apiName: 'WrfAPIGateway',
        path: '/parameter/',
        options: {
          headers: {
            Authorization: await getToken()!,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
          },
          queryParams: {
            "all":"true"//name: 'shandong'
          }
        }
      }).response;
      const result=await body.json()  as { [key: string]: any };
      const parameters:Parameter[]= result["para"];
      const auto_mode:string=result["auto"]["value"];
      console.log('print response:',auto_mode)
      let mode_type:boolean=false;
      setMode_type(auto_mode === "True");
      setError('');
      setParameters(parameters);
      
    }
    catch (e) {
      if (e instanceof Error) {
        setError(e.message);
        console.log(e)
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {   
    loadParameters();
  },[]);
  
  const handleModeChange = (e:boolean) => {
        if(e){
          setMode_type(true);          
          updateParameter("/event-driven-wrf/auto_mode","True");                 
        }else{
          setMode_type(false);          
          updateParameter("/event-driven-wrf/auto_mode","False");                        
        }
        
  };

  const handleParameterEditClose = () => {
    setShowUpdateModal(false);
  };
  const handleEditParameter = (parameter:Parameter) => {
    setParameter(parameter);
    console.log('parameter before save: ', parameter);
    setShowUpdateModal(true);
  };
  const handleSaveParameter = (parameter:Parameter) => {
    setParameter(parameter);
    console.log('parameter after save: ', parameter);
    updateParameter(parameter.description,parameter.value);
    loadParameters();
    setParameter({ ...parameter });
    setShowUpdateModal(false);
  };




  return (
    <>
      <View padding="1rem">
        <Heading color="#333" level={5} > Parameters Setting </Heading>
      </View>
      
      <View
        backgroundColor="var(--amplify-colors-white)"
        borderRadius="6px"
        maxWidth="100%"
        padding="1rem"
        minHeight="80vh"
      >
        <br></br>
        <SwitchField
          isDisabled={false}
          label="Auto Enabled"
          labelPosition="start"
          isChecked={mode_type}
          onChange={(e) => handleModeChange(e.target.checked)}
        />
        <br></br>
        <br></br>
        <ScrollView width="100%">        
          <ParaTable parameters= { parameters } onEdit = { handleEditParameter }/>
        </ScrollView>
        <br></br>
        <Divider orientation="horizontal" />
        <br></br>


      </View>
      {/* if parameter is not null*/}

      { parameter &&
      <Modal show={showUpdateModal} onHide={handleParameterEditClose} >
        <View
          backgroundColor="var(--amplify-colors-white)"
          borderRadius="6px"
          maxWidth={{ base: "100%", large: "100%" }}
          padding="1rem"
        >
          <Heading color="#333"> Modify Parameter</Heading>
          <br></br>
          <EditParameter parameter={parameter} onCancel={handleParameterEditClose} onSave={handleSaveParameter}/>
        </View> 
      </Modal>
      }
    </>
  );
};

export default Tasks;
