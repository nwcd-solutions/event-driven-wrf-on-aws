import React, { useEffect, useState } from "react";
import {
  View,
  Grid,
  Flex,
  Card,
  Placeholder,
  useTheme,
  Loader,
  Heading,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody
} from "@aws-amplify/ui-react";
import { MdPermIdentity,MdThumbUp ,MdThumbDown} from "react-icons/md";
import { Statistics } from "./Data";
import MiniStatistics from "./MiniStatistics";
import TrafficSources from "./TrafficSources";

import { get } from 'aws-amplify/api';
import "./Dashboard.css";

interface SettingsProps {
  getToken: () => void;
}
/// Mock Data
const barChartDataDemo = [
  {
    name: "Web",
    data: [
      11, 8, 9, 10, 3, 11, 11, 11, 12, 13, 2, 12, 5, 8, 22, 6, 8, 6, 4, 1, 8,
      24, 29, 51, 40, 47, 23, 26, 50, 26, 22, 27, 46, 47, 81, 46, 40,
    ],
  },
  {
    name: "Social",
    data: [
      7, 5, 4, 3, 3, 11, 4, 7, 5, 12, 12, 15, 13, 12, 6, 7, 7, 1, 5, 5, 2, 12,
      4, 6, 18, 3, 5, 2, 13, 15, 20, 47, 18, 15, 11, 10, 9,
    ],
  },
  {
    name: "Other",
    data: [
      4, 9, 11, 7, 8, 3, 6, 5, 5, 4, 6, 4, 11, 10, 3, 6, 7, 5, 2, 8, 4, 9, 9, 2,
      6, 7, 5, 1, 8, 3, 12, 3, 4, 9, 7, 11, 10,
    ],
  },
];



const getChartData = () =>
  new Promise((resolve, reject) => {
    if (!barChartDataDemo) {
      return setTimeout(() => reject(new Error("no data")), 750);
    }

    setTimeout(() => resolve(Object.values(barChartDataDemo)), 750);
  });

const Dashboard = ({ getToken }: SettingsProps) => {
  const [barChartData, setBarChartData] = useState<any | null>(null);
  const [trafficSourceData, setTrafficSourceData] = useState<any | null>(null);
  const [error, setError] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [stat, setStat] = useState<Statistics>(
    {
      last_7d_failed: "0",
      last_7d_success: "0",
      last_day_success: [],
      last_day_failed: [],

    }
  )
  const { tokens } = useTheme();

  async function loadStaticstics() {
    setLoading(true);

    try {
      const { body } = await get({
        apiName: 'WrfAPIGateway',
        path: '/task/',
        options: {
          headers: {
            Authorization: await getToken()!,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
          },

        }
      }).response;
      setLoading(true);
      const result = await body.json() as { [key: string]: any };
      console.log("get all statistics:", result);
      const data: Statistics = {
        last_7d_failed: result['last_7d_failed'],
        last_7d_success: result['last_7d_success'],
        last_day_success: result['last_day_success'],
        last_day_failed: result['last_day_failed'],
      }
      console.log("statistics success record:", data.last_day_success);
      setError('');
      setStat(data);
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
    loadStaticstics();

    const doChartData = async () => {
      const result = await getChartData();
      setBarChartData(result);
      setTrafficSourceData([112332, 123221, 432334, 342334, 133432]);
    };

    doChartData();
  }, []);

  return (
    <>
      <View padding="1rem">
        <Heading color="#333" level={5} > Dashboard </Heading>
      </View>

      <View borderRadius="6px" maxWidth="100%" padding="0rem" minHeight="100vh">

        <Grid
          templateColumns={{ base: "1fr", large: "1fr 1fr 1fr" }}
          templateRows={{ base: "repeat(4, 10rem)", large: "repeat(3, 8rem)" }}
          gap={tokens.space.xl}
        >
          <View rowSpan={{ base: 1, large: 1 }}>
            <MiniStatistics
              title="Success Tasks(last 7 days)"
              amount={stat.last_7d_success}
              icon={<MdThumbUp />}
              loading={loading}
            />
          </View>
          <View rowSpan={{ base: 1, large: 1 }}>
            <MiniStatistics title="Failed Tasks(last 7 days)" amount={stat.last_7d_failed} icon={<MdThumbDown />} loading={loading}/>
          </View>
          <View rowSpan={{ base: 1, large: 1 }}>
            <MiniStatistics
              title="Execution Time Per Day"
              amount="23,762"
              icon={<MdPermIdentity />}
              loading={loading}
            />
          </View>

          <View columnSpan={[1, 1, 1, 2]} rowSpan={{ base: 3, large: 4 }}>
            <Card borderRadius="15px">
              <div className="card-title">Tasks Executation Records in Last 24 Hours</div>
              <br></br>
              <Flex direction="column" minHeight="285px">
              {loading?
                <Loader 
                  size="large"
                  variation="linear"
                />
                :
                <View>
                  <Heading color="green" level={6} > Successed Task </Heading>
                  <br></br>

                  {stat.last_day_success.length === 0 ?
                    <View>
                      <br></br>
                      <h6>No Record Found</h6>
                      <br></br>
                    </View>
                    :
                    <Table caption="" highlightOnHover={false}>
                      <TableHead>
                        <TableRow>
                          <TableCell as="th">Ftime</TableCell>
                          <TableCell as="th">Trigger Time</TableCell>
                          <TableCell as="th">Cluster Ready Time</TableCell>
                          <TableCell as="th">Job Finished Time</TableCell>
                          <TableCell as="th">Run Duration</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {stat.last_day_success.map((item) => (
                          <TableRow key={item.receive_time}>
                            <TableCell>{item.ftime}</TableCell>
                            <TableCell>{item.receive_time}</TableCell>
                            <TableCell>{item.cluster_created_time}</TableCell>
                            <TableCell>{item.job_finished_time}</TableCell>
                            <TableCell>{item.run_duration}</TableCell>
                          </TableRow>
                        )
                        )}
                      </TableBody>
                    </Table>
                  }
                  <br></br>
                  <Heading color="red" level={6} > Failed Task </Heading>
                  <br></br>
                  {stat.last_day_failed.length === 0 ?
                    <View>
                      <br></br>
                      <h6>No Record Found</h6>
                      <br></br>
                    </View>
                    :
                    <Table >
                      <TableHead>
                        <TableRow>
                          <TableCell as="th">Trigger Time</TableCell>
                          <TableCell as="th">Reason</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {stat.last_day_failed.map((item2) => (
                          <TableRow key={item2.receive_time}>
                            <TableCell>{item2.receive_time}</TableCell>
                            <TableCell>{item2.reason.toString()}</TableCell>
                          </TableRow>
                        )
                        )}
                      </TableBody>
                    </Table>
                  }
                </View>
              }
              </Flex>
            </Card>
          </View>
          <View rowSpan={{ base: 1, large: 4 }}>
            <Card height="100%" borderRadius="15px">
              <div className="card-title">Analytics</div>
              <div className="chart-wrap">
                {barChartData ? (
                  <TrafficSources
                    title="Traffic Sources"
                    data={trafficSourceData}
                    type="donut"
                    labels={[
                      "Direct",
                      "Internal",
                      "Referrals",
                      "Search Engines",
                      "Other",
                    ]}
                  />
                ) : (
                  <Flex direction="column" minHeight="285px">
                    <Placeholder size="small" />
                    <Placeholder size="small" />
                    <Placeholder size="small" />
                    <Placeholder size="small" />
                  </Flex>
                )}
              </div>
            </Card>
          </View>
        </Grid>
      </View>
    </>
  );
};

export default Dashboard;
