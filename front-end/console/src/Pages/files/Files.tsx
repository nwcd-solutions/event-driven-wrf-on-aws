import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Heading, Flex,
  Button,
  Table,
  Icon,
  TableHead,
  TableBody,
  TableCell,
  TableRow,
  View,
  Menu,
  MenuButton,
  Loader,
  MenuItem,
} from '@aws-amplify/ui-react';
import { Modal } from 'react-bootstrap';
import { StorageManager } from '@aws-amplify/ui-react-storage';
import '@aws-amplify/ui-react/styles.css';
import { list } from 'aws-amplify/storage';
import { FcFolder, FcFile } from "react-icons/fc";
import { MdDelete } from "react-icons/md";
import { MdArrowDropDown } from "react-icons/md";
import { AiOutlineSortAscending } from "react-icons/ai";

export function Files() {

  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);
  const [files, setFiles] = useState<any[]>([]);
  const [upload, setUpload] = useState<boolean>(false);
  const [showModal, setShowModal] = useState(false)
  async function listfiles() {
    setLoading(true);
    try {
      const result = await list({
        prefix: ""
      });
      console.log('Listed Items:', result.items);
      const filesystem = {};
      let files: any[] = [];
      let prefix = ""
      result.items.forEach((res) => {
        let a = res.key;
        if (res.key.startsWith(prefix)) {
          a = res.key.slice(prefix.length);
        }
        if (a != "") {
          const elements = a.split('/');
          const element = elements.shift();
          console.log(element);
          console.log(elements);

          if (elements.length == 1) {
            if (!files.some((item) => item.name === element)) {
              let data = {
                name: element,
                size: '',
                modifydate: res.lastModified?.toString(),
                type: "aolder",
              };
              files.push(data);
            }

          }
          else if (elements.length == 0) {
            let data = {
              name: element,
              size: (res.size ? res.size / 1000 : 0).toFixed(1) + ' KB',
              modifydate: res.lastModified?.toString(),
              type: "file",
            };
            files.push(data);
          }
        }

      });
      files.sort((a, b) => {
        if (a.type === b.type) {
          return a.name.localeCompare(b.name);
        }
        return a.type - b.type;
      });
      setFiles(files);
      console.log(files);


    }
    catch (e) {
      if (e instanceof Error) {
        setError(e.message);
        console.log(e)
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    listfiles();
    setUpload(false);
  }, [upload]);

  const handleCreate = () => {
    setShowModal(true);
    //navigate("/fileupload");
  };

  const handleParameterEditClose = () => {
    setShowModal(false);
  };
  const handleComplete = (file: any) => {
    setShowModal(false);
    listfiles();
  }

  const handleCancel = () => {
    setShowModal(false);
  
  }

  return (
    <>
      <View padding="1rem">
        <Heading color="#333" level={5} > Post Processing Scripts </Heading>
      </View>
      {loading ?
        <Loader
          size="large"
          variation="linear"
        />
        :
        <View
          backgroundColor="var(--amplify-colors-white)"
          borderRadius="6px"
          maxWidth="100%"
          padding="1rem"
          minHeight="80vh"
        >
          <View >
            <br></br>
            <Flex justifyContent="flex-end">
              <Button onClick={() => { handleCreate() }} size="small">Upload File</Button>
              <Menu
                menuAlign="end"
                width="200"
                trigger={
                  <MenuButton size="small">
                    Action
                    <Icon fontSize={20} as={MdArrowDropDown}></Icon>
                  </MenuButton>
                }
              >
                <MenuItem fontSize={12}>Edit</MenuItem>
                <MenuItem fontSize={12}>Delete</MenuItem>
              </Menu>
            </Flex>
            <br></br>
          </View>
          <Table caption="" highlightOnHover={false} size="small">
            <TableHead>
              <TableRow>
                <TableCell width="40%" as="th">Name <AiOutlineSortAscending fontSize={20} /></TableCell>
                <TableCell textAlign={"right"} width="10%" as="th">Size</TableCell>
                <TableCell textAlign={"right"} width="40%" as="th">Last Modify Date</TableCell>
                <TableCell as="th" width="10%"></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {files?.map((item) => {
                return (
                  <TableRow key={item.name}>
                    <TableCell>
                      <Flex >
                        {item.type == 'aolder' ? <Icon width="10" size="small" as={FcFolder} /> : <Icon width="10" size="large" as={FcFile} />}

                        {item.name}
                      </Flex>
                    </TableCell>
                    <TableCell textAlign={"right"}>{item.size}</TableCell>
                    <TableCell textAlign={"right"}>{item.modifydate}   </TableCell>
                    <TableCell>


                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </View>
      }
      <Modal show={showModal} onHide={handleParameterEditClose} >
        <View width="600"
          backgroundColor="var(--amplify-colors-white)"
          borderRadius="6px"
          maxWidth={{ base: "100%", large: "100%" }}
          padding="1rem"
        >
          <Heading color="#333"> Modify Parameter</Heading>
          <br></br>
          <StorageManager
            accessLevel="guest"
            maxFileCount={1}
            path="scripts/"
            onUploadSuccess={handleComplete}
            isResumable
          />
          <br></br>
          <br></br>
          <Button onClick={ ()=> { handleCancel()}} >Cancel</Button>
        </View>
      </Modal>
    </>
  );
};
export default Files;
