const EMAIL_SAMPLES = [
  {
    name: "Legitimate Gmail",
    header: `From: Google Alerts <alerts@gmail.com>
To: user@example.com
Subject: New sign-in detected
Date: Tue, 02 Feb 2026 10:12:45 +0000
Authentication-Results: spf=pass dkim=pass dmarc=pass
Received: from mail-lf1-f44.google.com (209.85.167.44)
 by mx.example.com; Tue, 02 Feb 2026 10:12:45 +0000`
  },

  {
    name: "Corporate Mail",
    header: `From: IT Support <it@company.com>
To: staff@example.com
Subject: Password expiry notice
Date: Tue, 02 Feb 2026 09:02:11 +0000
Authentication-Results: spf=pass dkim=pass dmarc=pass
Received: from mail.company.com (198.51.100.21)
 by mx.example.com; Tue, 02 Feb 2026 09:02:11 +0000`
  },

  {
    name: "Marketing Campaign",
    header: `From: Deals <promo@shop-online.xyz>
To: user@example.com
Subject: Limited offer – verify now
Date: Mon, 01 Feb 2026 22:41:09 +0000
Authentication-Results: spf=softfail dkim=fail dmarc=fail
Received: from unknown.xyz (203.0.113.45)
 by relay1.mail.net;
Received: from relay1.mail.net (185.199.110.153)
 by mx.example.com; Mon, 01 Feb 2026 22:41:09 +0000`
  },

  {
    name: "Phishing Attempt",
    header: `From: Security Team <security@secure-login.click>
To: victim@example.com
Subject: Urgent – account suspended
Date: Sun, 31 Jan 2026 03:12:55 +0000
Authentication-Results: spf=fail dkim=fail dmarc=fail
Received: from attacker.click (91.214.124.17)
 by smtp.fake.net;
Received: from smtp.fake.net (45.9.148.221)
 by mx.example.com; Sun, 31 Jan 2026 03:12:55 +0000`
  },

  {
    name: "Internal Relay",
    header: `From: HR <hr@company.com>
To: staff@example.com
Subject: Policy update
Date: Mon, 01 Feb 2026 12:00:00 +0000
Authentication-Results: spf=pass dkim=pass dmarc=pass
Received: from internal.company.com (10.0.0.5)
 by mail.company.com;
Received: from mail.company.com (198.51.100.22)
 by mx.example.com; Mon, 01 Feb 2026 12:00:00 +0000`
  },

  {
  name: "Bank Notification (Legitimate)",
  header: `From: Axis Bank <alerts@axisbank.com>
To: user@example.com
Subject: Transaction Alert – ₹5,000 Debited
Date: Wed, 03 Feb 2026 14:15:22 +0000
Authentication-Results: spf=pass dkim=pass dmarc=pass
Received: from mail.axisbank.com (103.27.44.91)
 by mx.example.com; Wed, 03 Feb 2026 14:15:22 +0000`
},

{
  name: "3-Hop Marketing Campaign",
  header: `From: Deals <promo@shop-now.xyz>
To: user@example.com
Subject: Flash Sale!
Date: Tue, 02 Mar 2026 10:15:00 +0000
Authentication-Results: spf=softfail dkim=fail dmarc=fail
Received: from mail.shop-now.xyz (203.0.113.45)
 by relay1.mail.net;
Received: from relay1.mail.net (185.199.110.153)
 by mx.example.com;
Received: from mx.example.com (198.51.100.20)
 by destination.server.com;`
},

{
  name: "3-Hop SaaS Platform",
  header: `From: Notion <no-reply@notion.so>
To: user@example.com
Subject: Workspace Shared
Date: Tue, 02 Mar 2026 11:20:00 +0000
Authentication-Results: spf=pass dkim=pass dmarc=pass
Received: from mail.notion.so (104.26.10.78)
 by edge.notion.net;
Received: from edge.notion.net (172.67.210.55)
 by mx.example.com;
Received: from mx.example.com (142.250.200.9)
 by destination.server.com;`
},


{
  name: "4-Hop Corporate Relay",
  header: `From: IT Support <it@enterprise.com>
To: staff@example.com
Subject: Password Reset Required
Date: Wed, 03 Mar 2026 08:45:00 +0000
Authentication-Results: spf=pass dkim=pass dmarc=pass
Received: from smtp.enterprise.com (198.51.100.21)
 by edge.enterprise.com;
Received: from edge.enterprise.com (203.0.113.10)
 by gateway.enterprise.com;
Received: from gateway.enterprise.com (104.21.45.67)
 by mx.example.com;
Received: from mx.example.com (142.250.180.5)
 by destination.server.com;`
},

{
  name: "4-Hop Financial Alert",
  header: `From: Axis Bank <alerts@axisbank.com>
To: user@example.com
Subject: Transaction Alert
Date: Wed, 03 Mar 2026 12:00:00 +0000
Authentication-Results: spf=pass dkim=pass dmarc=pass
Received: from mail.axisbank.com (103.27.44.91)
 by secure.axisbank.com;
Received: from secure.axisbank.com (45.12.11.199)
 by gateway.bank.net;
Received: from gateway.bank.net (104.26.33.12)
 by mx.example.com;
Received: from mx.example.com (142.250.110.27)
 by destination.server.com;`
},


{
  name: "5-Hop Phishing Chain",
  header: `From: PayPal <security@paypaI.com>
To: victim@example.com
Subject: Account Suspended
Date: Thu, 04 Mar 2026 01:15:00 +0000
Authentication-Results: spf=fail dkim=fail dmarc=fail
Received: from paypaI.com (102.165.33.19)
 by smtp.fraud.net;
Received: from smtp.fraud.net (45.77.12.98)
 by relay1.scam.net;
Received: from relay1.scam.net (185.199.108.153)
 by relay2.scam.net;
Received: from relay2.scam.net (104.21.33.12)
 by mx.example.com;
Received: from mx.example.com (142.250.200.9)
 by destination.server.com;`
},

{
  name: "5-Hop Malware Delivery",
  header: `From: Invoice Dept <billing@invoice-secure.cc>
To: victim@example.com
Subject: Invoice Attached
Date: Thu, 04 Mar 2026 03:20:00 +0000
Authentication-Results: spf=fail dkim=fail dmarc=fail
Received: from origin.node.cc (185.222.58.101)
 by smtp1.node.cc;
Received: from smtp1.node.cc (91.109.204.77)
 by relay.global.net;
Received: from relay.global.net (185.199.110.153)
 by edge.global.net;
Received: from edge.global.net (104.21.45.67)
 by mx.example.com;
Received: from mx.example.com (142.250.190.14)
 by destination.server.com;`
},



{
  name: "6-Hop Advanced Threat",
  header: `From: Security Team <alert@secure-login.click>
To: victim@example.com
Subject: Urgent Verification Needed
Date: Fri, 05 Mar 2026 02:10:00 +0000
Authentication-Results: spf=fail dkim=fail dmarc=fail
Received: from node1.attack.cc (185.222.58.101)
 by node2.attack.cc;
Received: from node2.attack.cc (91.109.204.77)
 by relay1.global.net;
Received: from relay1.global.net (185.199.110.153)
 by relay2.global.net;
Received: from relay2.global.net (104.21.45.67)
 by edge.global.net;
Received: from edge.global.net (172.67.210.55)
 by mx.example.com;
Received: from mx.example.com (142.250.110.27)
 by destination.server.com;`
},

{
  name: "6-Hop Crypto Scam",
  header: `From: Investment Team <profits@crypto-double.io>
To: victim@example.com
Subject: Double Your Bitcoin
Date: Fri, 05 Mar 2026 04:40:00 +0000
Authentication-Results: spf=fail dkim=softfail dmarc=fail
Received: from crypto-double.io (91.201.67.88)
 by smtp.scam.net;
Received: from smtp.scam.net (45.9.148.221)
 by relay1.scam.net;
Received: from relay1.scam.net (185.199.108.153)
 by relay2.scam.net;
Received: from relay2.scam.net (104.21.33.12)
 by edge.scam.net;
Received: from edge.scam.net (172.67.210.55)
 by mx.example.com;
Received: from mx.example.com (142.250.200.9)
 by destination.server.com;`
},



{
  name: "3-Hop Newsletter",
  header: `From: Tech Weekly <newsletter@techweekly.com>
To: user@example.com
Subject: Cybersecurity Digest
Date: Sat, 06 Mar 2026 10:00:00 +0000
Authentication-Results: spf=pass dkim=pass dmarc=pass
Received: from mail.techweekly.com (192.0.2.55)
 by relay.news.net;
Received: from relay.news.net (104.21.45.67)
 by mx.example.com;
Received: from mx.example.com (142.250.180.5)
 by destination.server.com;`
},

{
  name: "4-Hop Office 365 Alert",
  header: `From: Microsoft <account-security@office.com>
To: user@example.com
Subject: Login Alert
Date: Sat, 06 Mar 2026 12:15:00 +0000
Authentication-Results: spf=pass dkim=pass dmarc=pass
Received: from outlook.office365.com (40.97.132.12)
 by edge.office.com;
Received: from edge.office.com (104.26.33.12)
 by gateway.office.com;
Received: from gateway.office.com (172.67.210.55)
 by mx.example.com;
Received: from mx.example.com (142.250.190.14)
 by destination.server.com;`
},

{
  name: "5-Hop Social Media Notification",
  header: `From: Facebook <notification@facebookmail.com>
To: user@example.com
Subject: New Login Detected
Date: Sun, 07 Mar 2026 08:00:00 +0000
Authentication-Results: spf=pass dkim=pass dmarc=pass
Received: from mail.facebook.com (31.13.71.36)
 by edge.facebook.com;
Received: from edge.facebook.com (157.240.1.35)
 by relay.facebook.net;
Received: from relay.facebook.net (104.21.45.67)
 by gateway.social.net;
Received: from gateway.social.net (172.67.210.55)
 by mx.example.com;
Received: from mx.example.com (142.250.110.27)
 by destination.server.com;`
}

];
