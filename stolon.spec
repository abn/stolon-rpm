%global commit      fec51408a83e6909c51e62ff54127d89748148fc
%global shortcommit %(c=%{commit}; echo ${c:0:7})

%define debug_package %{nil}
%define go_path %{_builddir}/go
%define go_package github.com/sorintlab/stolon
%define go_package_src %{go_path}/src/%{go_package}

Name:           stolon
Version:        0.7.0
Release:        1.%{shortcommit}%{?dist}
Summary:        PostgreSQL cloud native High Availability

Group:          System Environment/Daemons
License:        APLv2.0
URL:            https://github.com/sorintlab/stolon
Source0:        https://github.com/sorintlab/stolon/archive/%{commit}.tar.gz
Source1:        stolon-keeper.service
Source2:        stolon-keeper.sysconfig
Source3:        stolon-proxy.service
Source4:        stolon-proxy.sysconfig
Source5:        stolon-sentinel.service
Source6:        stolon-sentinel.sysconfig
Source7:        cluster-config.json

BuildRequires: golang git
BuildRequires: bash gcc-c++
BuildRequires: systemd-units

Requires(pre): shadow-utils
Requires:      systemd glibc

%package keeper
Summary: stolon keeper
Requires(pre): stolon = %{version}

%package proxy
Summary: stolon proxy
Requires(pre): stolon = %{version}

%package sentinel
Summary: stolon sentinel
Requires(pre): stolon = %{version}

%description
stolon is a cloud native PostgreSQL manager for PostgreSQL high availability.
It's cloud native because it'll let you keep an high available PostgreSQL inside
your containers (kubernetes integration) but also on every other kind of
infrastructure (cloud IaaS, old style infrastructures etc...)

%description keeper
Keeper manages a PostgreSQL instance converging to the clusterview provided by the sentinel(s).

%description proxy
Proxy is the client's access point. It enforce connections to the right PostgreSQL master and forcibly closes connections to unelected masters.

%description sentinel
Sentinel discovers and monitors keepers and calculates the optimal clusterview

%prep
%autosetup -n %{name}-%{commit}
mkdir -p %{go_package_src}
cp -R * %{go_package_src}/.

%build
export GOPATH=%{go_path}
cd %{go_package_src}
bash -x build

%install
install -d %{buildroot}/%{_bindir}
install -d %{buildroot}/%{_sharedstatedir}/%{name}
install %{go_package_src}/bin/stolonctl %{buildroot}/%{_bindir}

# keeper
install %{go_package_src}/bin/stolon-keeper %{buildroot}/%{_bindir}
install -D %{SOURCE1} %{buildroot}/%{_unitdir}/%{name}-keeper.service
install -D %{SOURCE2} %{buildroot}/%{_sysconfdir}/sysconfig/%{name}-keeper
install -d %{buildroot}/%{_sysconfdir}/%{name}/secrets
touch %{buildroot}/%{_sysconfdir}/%{name}/secrets/pgpass.{postgres,replication}

# proxy
install %{go_package_src}/bin/stolon-proxy %{buildroot}/%{_bindir}
install -D %{SOURCE3} %{buildroot}/%{_unitdir}/%{name}-proxy.service
install -D %{SOURCE4} %{buildroot}/%{_sysconfdir}/sysconfig/%{name}-proxy

# sentinel
install %{go_package_src}/bin/stolon-sentinel %{buildroot}/%{_bindir}
install -D %{SOURCE5} %{buildroot}/%{_unitdir}/%{name}-sentinel.service
install -D %{SOURCE6} %{buildroot}/%{_sysconfdir}/sysconfig/%{name}-sentinel
install -D %{SOURCE7} %{buildroot}/%{_sysconfdir}/%{name}/cluster-config.json

%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
    useradd -r -g %{name} -d %{_sharedstatedir}/%{name} -s /sbin/nologin \
    -c "stolon user" %{name}
exit 0

%postun
getent passwd %{name} >/dev/null && userdel %{name}
getent group %{name} >/dev/null && groupdel %{name}

%post keeper
%systemd_post %{name}-keeper.service

%preun keeper
%systemd_preun %{name}-keeper.service

%postun keeper
%systemd_postun_with_restart %{name}-keeper.service

%post proxy
%systemd_post %{name}-proxy.service

%postun proxy
%systemd_postun_with_restart %{name}-proxy.service

%preun proxy
%systemd_preun %{name}-proxy.service

%post sentinel
%systemd_post %{name}-sentinel.service

%preun sentinel
%systemd_preun %{name}-sentinel.service

%postun sentinel
%systemd_postun_with_restart %{name}-sentinel.service

%clean
rm -rf %{go_package_src}
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%attr(755, root, root) %{_bindir}/stolonctl
%dir %attr(750, %{name}, %{name}) %{_sysconfdir}/%{name}

%files keeper
%defattr(-,root,root,-)
%dir %attr(750, %{name}, %{name}) %{_sharedstatedir}/%{name}
%attr(755, root, root) %{_bindir}/stolon-keeper
%attr(644, root, root) %{_unitdir}/%{name}-keeper.service
%config(noreplace) %attr(640, root, %{name}) %{_sysconfdir}/sysconfig/%{name}-keeper
%config(noreplace) %attr(640, %{name}, %{name}) %{_sysconfdir}/%{name}/secrets/pgpass.postgres
%config(noreplace) %attr(640, %{name}, %{name}) %{_sysconfdir}/%{name}/secrets/pgpass.replication

%files proxy
%defattr(-,root,root,-)
%attr(755, root, root) %{_bindir}/stolon-proxy
%attr(644, root, root) %{_unitdir}/%{name}-proxy.service
%config(noreplace) %attr(640, root, %{name}) %{_sysconfdir}/sysconfig/%{name}-proxy

%files sentinel
%defattr(-,root,root,-)
%attr(755, root, root) %{_bindir}/stolon-sentinel
%attr(644, root, root) %{_unitdir}/%{name}-sentinel.service
%config(noreplace) %attr(640, %{name}, %{name}) %{_sysconfdir}/sysconfig/%{name}-sentinel
%attr(640, root, %{name}) %{_sysconfdir}/%{name}/cluster-config.json

%doc

%changelog
* Mon Sep 04 2017 Gregory Collins <greg@gregorycollins.net> - 0.7.0-1.fec5140
- upgrade to v0.7.0

* Sat Jun 03 2017 Arun Babu Neelicattu <arun.neelicattu@gmail.com> - 0.6.0-1.8420cb1
- upgrade to v0.6.0

* Thu Dec 15 2016 Arun Babu Neelicattu <arun.neelicattu@gmail.com> - 0.5.0-1.80b8649
- upgrade to v0.5.0

* Thu Nov 10 2016 Arun Babu Neelicattu <arun.neelicattu@gmail.com> - 0.4.0-1.0fba930
- upgrade to v0.4.0

* Fri Sep 30 2016 Arun Babu Neelicattu <arun.neelicattu@gmail.com> - 0.3.0-1.a3f1399
- update to v0.3.0

* Sun Aug 21 2016 Arun Babu Neelicattu <arun.neelicattu@gmail.com> - 0.2.0-2.b240c37
- clean up resources and add more comments

* Sat Aug 20 2016 Arun Babu Neelicattu <arun.neelicattu@gmail.com> - 0.2.0-1.b240c37
- intial version from master post 0.2.0 release

