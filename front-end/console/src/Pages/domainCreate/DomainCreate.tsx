import React,{ useEffect, useState } from "react";
import { View, Heading,Grid,TextField,Tabs,Button,Flex,Loader } from "@aws-amplify/ui-react";
import { useParams, useNavigate } from "react-router-dom";
import { Domain } from "../settings/Domain";
import { post } from 'aws-amplify/api';
import  Namelist  from "./Namelist";
import { en } from "@faker-js/faker";
import Location from "./Location";

interface DomainDetailProps {
  getToken:()=>void;
}

const DomainCreate = ({getToken}:DomainDetailProps) => {
  const navigate = useNavigate();
  let {id}=useParams() ;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);
  const [domain,setDomain] = useState<Domain>(new Domain());
  const [enableCreate,setEnableCreate]= useState<boolean>(false);
  async function CreateDomain() {
    setLoading(true);    
    try {        
      const { body } = await post({
        apiName: 'WrfAPIGateway',
        path: '/domain/',        
        options: {
          headers: {
            Authorization: await getToken()!,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
          },  
          body: {
            data:{
              model_config:JSON.stringify(domain)
            }            
          }               
        }
      }).response;   

      setError(''); 
    }
    catch (e) {
      if (e instanceof Error) {
        setError(e.message);
        console.log(e)
      }
    } finally {
      setLoading(false);
      navigate(-1);
    }
  }

  const validate =() => {
    if (domain !=null){
       if(domain.name!='' && domain.wps_namelist!='' && domain.wrf_namelist!='' && domain.wrf_bk_namelist!=''&& domain.location.length>0){
        setEnableCreate(true);
       }      
    }
  }
  const handleLocationUpdate =(location:any)=>{
    if (domain !=null){
      setDomain({...domain,location:location});
      if(domain.name!='' && domain.wps_namelist!='' && domain.wrf_namelist!='' && domain.wrf_bk_namelist!=''){
        setEnableCreate(true);
       }      
    }
  
  };
  const handleNamelistUpdate = (namelist:string,type:string) => {
    if (domain !=null){
      if (type=='wps'){
        setDomain({...domain,wps_namelist:namelist});
        if(domain.name!='' &&  domain.wrf_namelist!='' && domain.wrf_bk_namelist!=''&& domain.location.length>0){
          setEnableCreate(true);
         } 
      }else if (type=='wrf'){
        setDomain({...domain,wrf_namelist:namelist});
        if(domain.name!='' && domain.wps_namelist!=''  && domain.wrf_bk_namelist!=''&& domain.location.length>0){
          setEnableCreate(true);
         } 
      }else if(type=='wrf_bk'){
        setDomain({...domain,wrf_bk_namelist:namelist});
        if(domain.name!='' && domain.wps_namelist!='' && domain.wrf_namelist!=''&& domain.location.length>0 ){
          setEnableCreate(true);
         } 
      }
      validate();
    }   
  };

  const handleCheck =  () => {
    console.log('update domain:',domain);
    //if (domain !=null){
    //  setDomain({...domain});
    //} 
  };

  const handleCancel = () => {
    navigate(-1);
  };

  const handleCreate = () =>{
    console.log('update new domain:',domain);
    
    if (domain !=null){
      if (domain.wps_namelist==''){
        alert("there is no wps namelist file");
      }
      else if (domain.wrf_namelist==''){
        alert("there is no wrf namelist file");
      }
      else if (domain.wrf_bk_namelist==''){
        alert("there is no wrf bk namelist file");
      }
      else{
        CreateDomain();
      }
      
    }  
  }
 
  const handleChange = (e: { target: { name: any; value: any; }; }) => {
    const { name, value } = e.target;
    if (domain !=null){
      setDomain({ ...domain, [name]: value });
      validate();
    }
  };  

  useEffect(() => { 

  },[]);

  return (
    <>    
      <View padding="1rem">
          <Heading color="#333" level={5}>Create New Domain</Heading>
      </View>
      { loading ? <Loader  size="large" variation="linear"></Loader> :
      <Grid
          columnGap="0.5rem"
          rowGap="0.5rem"
          templateColumns="1fr 1fr 1fr"
          templateRows="1fr 1fr 0.1fr"
          
      >
          <View
              backgroundColor="var(--amplify-colors-white)"
              borderRadius="6px"       
              padding="2rem"
              minHeight="50vh"
              columnStart="1"
              columnEnd="2"
              
          >
              <TextField label="Name" name="name" variation="quiet"  placeholder="Please input domain name" onChange={handleChange} width={'70%'}/>
              <br></br>
              <TextField label="Description" name="description" variation="quiet" placeholder="Please input description of domain" width={'70%'} onChange={handleChange} />
              <br></br>
              <TextField label="Cores" variation="quiet"  width={'70%'}/>
              <br></br>

          </View>
          <View
              backgroundColor="var(--amplify-colors-white)"
              borderRadius="6px"   
              padding="1rem"
              minHeight="50vh"
              columnStart="2"
              columnEnd="-1"
          >Map</View>
          <View
              backgroundColor="var(--amplify-colors-white)"
              borderRadius="6px"
              padding="2rem"
              columnStart="1"
              columnEnd="-1"
          >
              <Tabs
                  defaultValue={'Tab 1'}
                  items={[
                  { 
                      label: 'WPS Namelist', 
                      value: 'Tab 1', 
                      content:  domain?.wps_namelist ?
                                (<Namelist namelist={ domain?.wps_namelist} type={'wps'} onUpdate = {handleNamelistUpdate}></Namelist>) :
                                (<Namelist namelist={''} type={'wps'} onUpdate = {handleNamelistUpdate}></Namelist>)
                  },
                  { 
                      label: 'Primary WRF Namelist', 
                      value: 'Tab 2', 
                      content: domain?.wrf_namelist ?
                               (<Namelist namelist={ domain?.wrf_namelist} type={'wrf'} onUpdate = {handleNamelistUpdate}></Namelist>) :
                               (<Namelist namelist={ ''} type={'wrf'} onUpdate = {handleNamelistUpdate}></Namelist>)
                  },
                  { 
                      label: 'Second WRF Namelist', 
                      value: 'Tab 3', 
                      content: domain?.wrf_bk_namelist ?
                               (<Namelist namelist={ domain?.wrf_bk_namelist} type={'wrf_bk'} onUpdate = {handleNamelistUpdate}></Namelist>) :
                               (<Namelist namelist={ ''} type={'wrf_bk'} onUpdate = {handleNamelistUpdate}></Namelist>)
                  },
                  { 
                    label: 'Location', 
                    value: 'Tab 4', 
                    content: domain?.location ?
                             (<Location location={ domain?.location}  onUpdate = {handleLocationUpdate}></Location>) :
                             (<Location location={ []}  onUpdate = {handleLocationUpdate}></Location>)
                },
                  ]}
              />
          </View>
          <View
              backgroundColor="var(--amplify-colors-white)"
              borderRadius="6px"   
              padding="2rem"
              columnStart="1"
              columnEnd="-1"
          >
              <Flex justifyContent="flex-end">
                  <Button
                      width={'200px'}    
                      onClick={handleCancel}      
                  >Cancel</Button>
                  <Button
                      width={'200px'}      
                      onClick={handleCheck}    
                  >Duplicate</Button>
                  <Button
                      variation="primary" 
                      width={'200px'}   
                      isDisabled={!enableCreate} 
                      onClick={handleCreate}
                  >Create</Button>
              </Flex>
          </View>
      </Grid>
       }
    </>
  );
};

export default DomainCreate;
