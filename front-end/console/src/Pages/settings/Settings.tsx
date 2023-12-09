import React ,{ useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { View, Heading, ScrollView ,Divider,SwitchField,Text,Flex,Button,Loader } from "@aws-amplify/ui-react";
import ParaTable from "./ParameterList";
import DomainTable from "./DomainList";
import { Parameter } from "./Parameter"
import  EditParameter from "./ParameterEdit";
import { Domain } from "./Domain"
import { get,del,put } from 'aws-amplify/api';
import Forms from '../domainDetail';
import { Modal } from 'react-bootstrap';
interface SettingsProps {
  getToken:()=>void;
}

const Settings = ({getToken}:SettingsProps) => {

  const navigate = useNavigate();
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [parameter , setParameter] =useState<Parameter>();
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | undefined>(undefined);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [domainName, setDomainName] =useState<string | undefined>(undefined);
  const [mode_type,setMode_type] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false)
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
  async function loadDomains() {
    setLoading(true);
    
    try {        
      const { body } = await get({
        apiName: 'WrfAPIGateway',
        path: '/domain/',        
        options: {
          headers: {
            Authorization: await getToken()!,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
          },  
                
        }
      }).response;   
      setLoading(true);
      console.log("get all domains:",body.json());     
      const domains:Domain[]= await body.json() as Array<any>;
    
      setError('');
      setDomains(domains);
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

  async function deleteDomain(name:string) {
    setLoading(true);
    try {
     
      console.log('get token: ', await getToken());
      const response = await del({
        apiName: 'WrfAPIGateway',
        path: '/domain',
        options: {
          headers: {
            Authorization: await getToken()!,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
          },
          queryParams: {
            "configuration_name":name
          }
        }
      }).response;
      
      setDeleting(true);
      if (response.statusCode === 200) {
        console.log('delete response:',response) 
        setError('');        
        loadDomains();      
      }
     
    }
    catch (e) {
      if (e instanceof Error) {
        setError(e.message);
        console.log(e)
      }
    } finally {
      setDeleting(false);
      setShowDeleteModal(false);
    }
  }

  useEffect(() => {   
    loadParameters();
    loadDomains();
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
  const handleDeleteDomain =(name:string) => {    
    setShowDeleteModal(true);
    setDomainName(name);
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
        <Heading color="#333"> General Setting </Heading>
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

        <Heading color="#333"  > Domain Setting </Heading>
      { loading ? 
        <Loader 
            size="large"
            variation="linear"
        />  :
        <ScrollView width="100%">
          <DomainTable domains={ domains } onDelete = { handleDeleteDomain}/>
        </ScrollView>
      }
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
      { domainName &&
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)} >
        <View
          backgroundColor="var(--amplify-colors-white)"
          borderRadius="6px"
          maxWidth={{ base: "100%", large: "100%" }}
          padding="1rem"
        >
          <Heading color="#333"> Delete Domain</Heading>
          <br></br>
          <Text>
               Are you sure to delete domain {domainName}?
          </Text>
          <br></br>
          <br></br>       
          <Flex>
            <Button
              width={{ base: "100%", large: "50%" }}
              style={{ marginLeft: "auto" }}     
              onClick={() => setShowDeleteModal(false)}    
            >
              Cancel
            </Button>
            <Button
              variation="primary"
              colorTheme="error" 
              width={{ base: "100%", large: "50%" }}
              style={{ marginLeft: "auto" }}
              onClick={() => {deleteDomain(domainName)}}             
            >
              Confirm
            </Button>
          </Flex>
        </View> 
      
      </Modal>
      }
    </>
  );
};

export default Settings;
