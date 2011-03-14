#!/usr/bin/env python

import unittest
import bills
from os import path

class BillsTest(unittest.TestCase):

    session = '2011 Session'

    def setUp(self):
        self.bills = []
        self.s = bills.OREBillScraper(None)
        self.s.rawdataByYear[2011] = (
            open(path.join(path.dirname(__file__),'testdata/measures.txt')).read(),
            open(path.join(path.dirname(__file__),'testdata/meashistory.txt')).read()
        )
        # replace base class method for saving bill data
        self.s.save_bill = lambda b: self.bills.append(b)

    def testFtpPathResolution(self):
        # OR stores basic bill (measure) info on a FTP server
        # current year is in '/pub/measures.txt'
        # past years are in '/pub/archive/[xx]measures.txt' where xx is the two digit year
        # they'll have a Y2100 problem, but I will be dead by then
        self.assertEquals('measures.txt', self.s._resolve_ftp_path(2011, 2011))
        self.assertEquals('archive/01measures.txt', self.s._resolve_ftp_path(2001, 2011))
        self.assertEquals('archive/10measures.txt', self.s._resolve_ftp_path(2010, 2011))

    def testActionFtpPathResolution(self):
        self.assertEquals('meashistory.txt', self.s._resolve_action_ftp_path(2011, 2011))
        self.assertEquals('archive/01meashistory.txt', self.s._resolve_action_ftp_path(2001, 2011))
        self.assertEquals('archive/10meashistory.txt', self.s._resolve_action_ftp_path(2010, 2011))

    def _testCanParseHouse(self):
        self.s.scrape('lower', self.session)
        self.assertEquals(1637, len(self.bills))
        self._billEquals({
                'title' : 'Deletes requirement that Oregon Youth Authority make progress reports to Legislative Assembly.',
                'bill_id' : 'HB 2669',
                'session' : self.session,
                'chamber' : 'lower' }, self.bills[0])

    def _testCanParseSenate(self):
        self.s.scrape('upper', self.session)
        self.assertEquals(1012, len(self.bills))
        self._billEquals({
                'title' : 'Modifies terminology in education statutes for persons with intellectual disability.',
                'bill_id' : 'SB 0003',
                'session' : self.session,
                'chamber' : 'upper' }, self.bills[0])

    def testCanParseActions(self):
        actions = self.s.parse_actions(self.s.rawdataByYear[2011][1])
        self.assertEquals(7907, len(actions))
        self.assertEquals('HB 2659', actions[0]['bill_id'])
        self.assertEquals("First reading. Referred to Speaker's desk.", actions[0]['action'])
        self.assertEquals('2011-01-11 12:36:18', actions[0]['date'].strftime("%Y-%m-%d %H:%M:%S"))
        self.assertEquals('lower', actions[0]['actor'])

    def testCanGroupActionsByBill(self):
        actions_by_bill = self.s.parse_actions_and_group(self.s.rawdataByYear[2011][1])
        actions = actions_by_bill['HB 2659']
        self.assertEquals(2, len(actions))
        self.assertEquals("First reading. Referred to Speaker's desk.", actions[0]['action'])
        self.assertEquals("Referred to Judiciary.", actions[1]['action'])

    def testCanParseDocsAndSponsors(self):
        data = open(path.join(path.dirname(__file__),'testdata/bill-detail-1.html')).read()
        parser = bills.BillDetailsParser()
        parsed = parser.parse(data)
        self.assertEquals(4, len(parsed['versions']))
        self.assertEquals({'name': 'Introduced',
                           'url': 'http://www.leg.state.or.us/10ss1/measures/hb3600.dir/hb3623.intro.html' },
                          parsed['versions'][0])
        self.assertEquals({'name': 'Enrolled',
                           'url': 'http://www.leg.state.or.us/10ss1/measures/hb3600.dir/hb3623.en.html' },
                          parsed['versions'][1])
        self.assertEquals([ 'BARTON', 'J SMITH', 'ROSENBAUM' ], parsed['sponsors'])

    def testCanParseDocsAndSponsors2(self):
        data = open(path.join(path.dirname(__file__),'testdata/bill-detail-2.html')).read()
        parser = bills.BillDetailsParser()
        parsed = parser.parse(data)
        self.assertEquals(1, len(parsed['versions']))
        self.assertEquals({'name': 'Introduced',
                           'url': 'http://www.leg.state.or.us/11reg/measures/sb0100.dir/sb0140.intro.html' },
                          parsed['versions'][0])
        self.assertEquals([ ], parsed['sponsors'])

    def testCanParseDocsAndSponsors3(self):
        data = open(path.join(path.dirname(__file__),'testdata/bill-detail-3.html')).read()
        parser = bills.BillDetailsParser()
        parsed = parser.parse(data)
        self.assertEquals(1, len(parsed['versions']))
        self.assertEquals({'name': 'Introduced',
                           'url': 'http://www.leg.state.or.us/11reg/measures/hb2700.dir/hb2785.intro.html' },
                          parsed['versions'][0])
        self.assertEquals([ 'THATCHER' ], parsed['sponsors'])

    def testCanResolveDocsUrls(self):
        parser = bills.BillDetailsParser()
        input = [
            { 'session': '2011 Session', 'bill_id': 'HB 2659',
              'params': { 'lookfor': 'hb', 'number': '2659', 'lookin': '11reg', 'submit':'Search'} }
        ]
        for i in input:
            params = parser.resolve_search_params(i['session'], i['bill_id'])
            self.assertEquals(i['params'], params)

    def _testLoadFtpData(self):
        # this test is a little slow b/c it actually loads the
        # FTP file from OR's server.  the other tests should use files
        # in testdata
        self.s.rawdataByYear = { }
        data = self.s._load_data(self.session)
        self.assertTrue(data != None)
        self.assertEquals(0, data.find('Meas_Prefix'))

    def _billEquals(self, expected, actual):
        for k, v in expected.items():
            self.assertEqual(v, actual[k])
                
if __name__ == '__main__':
    unittest.main()
