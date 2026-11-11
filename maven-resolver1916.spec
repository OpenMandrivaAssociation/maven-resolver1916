Name:		maven-resolver1916
Version:	1.9.16
Release:	1
Summary:	Apache Maven Artifact Resolver 1.9.16 side jars
Group:		Development/Java
License:	Apache-2.0
URL:		https://maven.apache.org/resolver/
# GitHub tag maven-resolver-1.9.16, four modules only. The demo jar
# is not part of this archive. maven-components already ships the
# 1.9.16 API jar, so this package does not install that file.
Source0:	maven-resolver-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	mvn(org.apache.maven.resolver:maven-resolver-api) = %{version}
BuildRequires:	mvn(org.slf4j:slf4j-api) = 2.0.17
BuildRequires:	mvn(javax.inject:javax.inject)
BuildRequires:	mvn(org.eclipse.sisu:org.eclipse.sisu.inject) = 0.3.5
BuildRequires:	mvn(com.google.inject:guice) = 5.1.0
BuildRequires:	mvn(com.google.guava:guava) = 33.6.0-jre
BuildRequires:	mvn(com.google.guava:failureaccess) = 1.0.3
BuildRequires:	mvn(aopalliance:aopalliance)

Requires:	mvn(org.apache.maven.resolver:maven-resolver-api) = %{version}
Requires:	mvn(org.slf4j:slf4j-api) = 2.0.17

%description
org.apache.maven.resolver spi, util, named-locks, and impl at %{version}.
Gradle 9.9.1 pins maven-resolver-api %{version}, which maven-components
already provides. Maven 3.9.5 core also needs these three sibling jars
and the named-lock helper. The unversioned resolver indexes stay on the
newer resolver. This package installs versioned jars and versioned
sysjar indexes only.

%prep
%autosetup -n maven-resolver-%{version}
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
J=%{_javadir}
API=$J/maven-resolver-api-%{version}.jar
test -s "$API"

compile() {
	module="$1"
	expect="$2"
	cp="$3"
	find "$module/src/main/java" -name '*.java' ! -name 'module-info.java' > "$module.sources"
	test "$(wc -l < "$module.sources")" -eq "$expect"
	mkdir -p "$module/classes"
	javac --release 8 -encoding UTF-8 -Xlint:-options -proc:none -cp "$cp" -d "$module/classes" @"$module.sources"
	jar cf "$module.jar" -C "$module/classes" .
	jar i "$module.jar"
	jar tf "$module.jar" | grep -E '\.(java|jar|so|node|wasm)$' && exit 1 || true
}

compile maven-resolver-named-locks 13 "$J/slf4j-api.jar:$J/atinject.jar"
compile maven-resolver-spi 52 "$API"
compile maven-resolver-util 97 "$API"
compile maven-resolver-impl 118 "$API:maven-resolver-spi.jar:maven-resolver-util.jar:maven-resolver-named-locks.jar:$J/slf4j-api.jar:$J/atinject.jar:$J/org.eclipse.sisu.inject-0.3.5.jar:$J/google-guice.jar:$J/guava.jar:$J/failureaccess.jar:$J/aopalliance.jar"
javap -verbose -cp maven-resolver-util.jar org.eclipse.aether.util.version.GenericVersionScheme | grep -F -q 'major version: 52'

write_pom() {
	art="$1"
	shift
	cat > "$art.pom" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.apache.maven.resolver</groupId>
  <artifactId>$art</artifactId>
  <version>%{version}</version>
  <name>$art</name>
  <description>Apache Maven Artifact Resolver %{version}.</description>
  <licenses>
    <license>
      <name>Apache-2.0</name>
    </license>
  </licenses>
  <dependencies>
EOF
	for dep in "$@"; do
		IFS=: read -r g a v << EOF2
$dep
EOF2
		cat >> "$art.pom" << EOF
    <dependency>
      <groupId>$g</groupId>
      <artifactId>$a</artifactId>
      <version>$v</version>
    </dependency>
EOF
	done
	printf '%s\n' '  </dependencies>' '</project>' >> "$art.pom"
}

write_pom maven-resolver-named-locks \
	org.slf4j:slf4j-api:2.0.17
write_pom maven-resolver-spi \
	org.apache.maven.resolver:maven-resolver-api:%{version}
write_pom maven-resolver-util \
	org.apache.maven.resolver:maven-resolver-api:%{version}
write_pom maven-resolver-impl \
	org.apache.maven.resolver:maven-resolver-api:%{version} \
	org.apache.maven.resolver:maven-resolver-spi:%{version} \
	org.apache.maven.resolver:maven-resolver-util:%{version} \
	org.apache.maven.resolver:maven-resolver-named-locks:%{version} \
	org.slf4j:slf4j-api:2.0.17

%install
set -eo pipefail
: > .mfiles
install_one() {
	art="$1"
	sysjar install --buildroot %{buildroot} \
		--artifact "$art.pom:$art.jar" \
		--file-name "$art-%{version}" \
		--filelist ".mfiles-$art"
	/bin/mv "%{buildroot}/usr/share/sysjar/index/org.apache.maven.resolver/$art.sysjar" \
		"%{buildroot}/usr/share/sysjar/index/org.apache.maven.resolver/$art-%{version}.sysjar"
	sed -i "s|$art\\.sysjar|$art-%{version}.sysjar|" ".mfiles-$art"
	grep -F -q "\"version\": \"%{version}\"" "%{buildroot}/usr/share/sysjar/index/org.apache.maven.resolver/$art-%{version}.sysjar"
	test ! -e "%{buildroot}/usr/share/sysjar/index/org.apache.maven.resolver/$art.sysjar"
	while IFS= read -r line; do
		grep -qxF -- "$line" .mfiles || printf '%s\n' "$line" >> .mfiles
	done < ".mfiles-$art"
}
install_one maven-resolver-named-locks
install_one maven-resolver-spi
install_one maven-resolver-util
install_one maven-resolver-impl

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
J=%{_javadir}
SPI=%{buildroot}$J/maven-resolver-spi-%{version}.jar
UTIL=%{buildroot}$J/maven-resolver-util-%{version}.jar
LOCKS=%{buildroot}$J/maven-resolver-named-locks-%{version}.jar
IMPL=%{buildroot}$J/maven-resolver-impl-%{version}.jar
API=$J/maven-resolver-api-%{version}.jar
for jar in "$SPI" "$UTIL" "$LOCKS" "$IMPL" "$API"; do
	test -s "$jar"
done
mkdir -p check
cat > check/Res.java << 'END'
import java.util.concurrent.TimeUnit;
import org.eclipse.aether.internal.impl.DefaultArtifactResolver;
import org.eclipse.aether.named.NamedLock;
import org.eclipse.aether.named.providers.NoopNamedLockFactory;
import org.eclipse.aether.spi.log.NullLoggerFactory;
import org.eclipse.aether.util.version.GenericVersionScheme;
import org.eclipse.aether.version.Version;

public class Res {
	public static void main(String[] args) throws Exception {
		Version parsed = new GenericVersionScheme().parseVersion("1.9.16");
		NamedLock lock = new NoopNamedLockFactory().getLock("gradle");
		boolean shared = lock.lockShared(1, TimeUnit.MILLISECONDS);
		String logger = NullLoggerFactory.INSTANCE.getLogger("gradle").getClass().getSimpleName();
		DefaultArtifactResolver resolver = new DefaultArtifactResolver();
		resolver.setLoggerFactory(NullLoggerFactory.INSTANCE);
		lock.close();
		System.out.println("resolver1916_ok " + parsed + " " + lock.name() + " " + shared + " " + logger + " " + (resolver != null));
	}
}
END
CP="$API:$SPI:$UTIL:$LOCKS:$IMPL:$J/slf4j-api.jar"
javac --release 8 -encoding UTF-8 -Xlint:-options -proc:none -cp "$CP" -d check check/Res.java
java -cp "check:$CP" Res > check/out.txt
cat check/out.txt
grep -F -q 'resolver1916_ok 1.9.16 gradle true NullLogger true' check/out.txt

%files -f .mfiles
%doc LICENSE
