import React ,{ useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { View, Heading, ScrollView ,Text,Flex,Button,Loader } from "@aws-amplify/ui-react";
import DomainTable from "./DomainList";
import { Domain } from "./Domain"
import { get,del,put } from 'aws-amplify/api';
import { Modal } from 'react-bootstrap';
interface SettingsProps {
  getToken:()=>void;
}

const Settings = ({getToken}:SettingsProps) => {

  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | undefined>(undefined);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [domainName, setDomainName] =useState<string | undefined>(undefined);
  const [showDeleteModal, setShowDeleteModal] = useState(false)

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
    loadDomains();
  },[]);
  
  const handleDeleteDomain =(name:string) => {    
    setShowDeleteModal(true);
    setDomainName(name);
  };



  return (
    <>
      <View padding="1rem">
        <Heading color="#333" level={5} > Domain Configuration </Heading>
      </View>
      
      <View
        backgroundColor="var(--amplify-colors-white)"
        borderRadius="6px"
        maxWidth="100%"
        padding="1rem"
        minHeight="80vh"
      >
        
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
